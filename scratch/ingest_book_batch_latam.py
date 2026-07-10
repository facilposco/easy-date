#!/usr/bin/env python
"""Ingest a reviewed EPUB manifest into the Easy Date books RAG.

The runner is deliberately serial: SQLite and the local Chroma collection are
shared state, so concurrent book ingests can corrupt or overwrite progress.
It records every attempted book and can resume a stopped batch safely.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INGEST = ROOT / "books_kb" / "ingest_text_epub_latam.py"
ALLOWED_ACTIONS = {
    "ingest_without_translation_then_qa",
    "translate_to_latam_then_ingest_then_qa",
}


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "filename", "title", "author", "language", "category", "native_words_est",
        "status", "book_id", "report_path", "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def eligible_rows(manifest: dict, min_words: int) -> tuple[list[dict], list[dict]]:
    accepted: list[dict] = []
    deferred: list[dict] = []
    for row in manifest.get("rows", []):
        if row.get("extension") != ".epub" or row.get("duplicate_status") != "new":
            continue
        if row.get("recommended_action") not in ALLOWED_ACTIONS:
            continue
        if int(row.get("native_words_est") or 0) < min_words:
            deferred.append(row)
        else:
            accepted.append(row)
    return accepted, deferred


def report_from_stdout(stdout: str) -> tuple[int | None, str]:
    # Gemini retries can print progress before the final JSON report.
    starts = [index for index, char in enumerate(stdout) if char == "{" and (index == 0 or stdout[index - 1] == "\n")]
    for start in reversed(starts):
        try:
            payload = json.loads(stdout[start:])
        except json.JSONDecodeError:
            continue
        return payload.get("book_id"), str(payload.get("report_path", ""))
    return None, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--label", default=None)
    parser.add_argument("--min-native-words", type=int, default=500)
    parser.add_argument("--translation-provider", choices=["gemini", "google"], default="gemini")
    parser.add_argument("--translation-chars", type=int, default=1800)
    parser.add_argument("--allow-google-fallback", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="0 means process every eligible EPUB.")
    parser.add_argument("--resume-report", type=Path)
    parser.add_argument("--semantic-qa-report", type=Path, help="Only ingest books that passed this semantic QA report.")
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    eligible, deferred = eligible_rows(manifest, args.min_native_words)
    label = args.label or args.manifest.stem.replace("book_batch_manifest_", "")
    report_path = args.resume_report or DOCS / f"book_batch_ingestion_{label}_{stamp()}.json"
    existing = read_json(report_path) if report_path.exists() else {}
    completed_hashes = {
        item.get("md5")
        for item in existing.get("results", [])
        if item.get("status") == "ok" and item.get("md5")
    }
    results = [item for item in existing.get("results", []) if item.get("status") == "ok"]
    semantic_deferred: list[dict] = []
    if args.semantic_qa_report:
        semantic_payload = read_json(args.semantic_qa_report)
        allowed_titles = {
            str(row.get("book"))
            for row in semantic_payload.get("books", [])
            if row.get("status") in {"pass", "skipped_source_spanish"}
        }
        semantic_deferred = [
            row for row in eligible
            if row.get("md5") not in completed_hashes and row.get("title_guess") not in allowed_titles
        ]
        eligible = [row for row in eligible if row.get("md5") in completed_hashes or row.get("title_guess") in allowed_titles]
    if args.limit:
        eligible = eligible[: args.limit]

    for row in deferred:
        results.append({
            "md5": row.get("md5"),
            "filename": row.get("filename"),
            "title": row.get("title_guess"),
            "author": row.get("author_guess"),
            "language": row.get("language_guess"),
            "category": row.get("category_guess"),
            "native_words_est": row.get("native_words_est"),
            "status": "deferred_requires_ocr_or_manual_review",
            "book_id": "",
            "report_path": "",
            "error": "Native text extraction below batch threshold; do not index as text-only.",
        })

    for row in semantic_deferred:
        results.append({
            "md5": row.get("md5"),
            "filename": row.get("filename"),
            "title": row.get("title_guess"),
            "author": row.get("author_guess"),
            "language": row.get("language_guess"),
            "category": row.get("category_guess"),
            "native_words_est": row.get("native_words_est"),
            "status": "deferred_semantic_qa_review",
            "book_id": "",
            "report_path": "",
            "error": "Semantic QA did not pass or the book was not staged for review.",
        })

    for row in eligible:
        if row.get("md5") in completed_hashes:
            continue
        command = [
            sys.executable,
            str(INGEST),
            "--epub", row["path"],
            "--title", row["title_guess"],
            "--author", row.get("author_guess") or "Desconocido",
            "--translation-provider", args.translation_provider,
            "--translation-chars", str(args.translation_chars),
        ]
        if args.allow_google_fallback:
            command.append("--allow-google-fallback")
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, errors="replace")
        book_id, ingest_report = report_from_stdout(process.stdout)
        result = {
            "md5": row.get("md5"),
            "filename": row.get("filename"),
            "title": row.get("title_guess"),
            "author": row.get("author_guess"),
            "language": row.get("language_guess"),
            "category": row.get("category_guess"),
            "native_words_est": row.get("native_words_est"),
            "status": "ok" if process.returncode == 0 else "failed",
            "book_id": book_id or "",
            "report_path": ingest_report,
            "error": "" if process.returncode == 0 else (process.stderr or process.stdout)[-2500:],
        }
        results.append(result)
        save_json(report_path, {
            "generated_at": stamp(),
            "manifest": str(args.manifest),
            "batch_label": label,
            "translation_provider": args.translation_provider,
            "allow_google_fallback": args.allow_google_fallback,
            "semantic_qa_report": str(args.semantic_qa_report) if args.semantic_qa_report else "",
            "results": results,
        })

    csv_path = report_path.with_suffix(".csv")
    write_csv(csv_path, results)
    payload = read_json(report_path)
    payload["csv"] = str(csv_path)
    payload["summary"] = {
        "eligible": len(eligible),
        "ok": sum(item.get("status") == "ok" for item in results),
        "failed": sum(item.get("status") == "failed" for item in results),
        "deferred_requires_ocr_or_manual_review": sum(
            item.get("status") == "deferred_requires_ocr_or_manual_review" for item in results
        ),
        "deferred_semantic_qa_review": sum(
            item.get("status") == "deferred_semantic_qa_review" for item in results
        ),
    }
    save_json(report_path, payload)
    print(json.dumps({"report": str(report_path), "csv": str(csv_path), **payload["summary"]}, ensure_ascii=False))
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
