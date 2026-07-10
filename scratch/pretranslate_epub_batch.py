#!/usr/bin/env python
"""Prepare translations for a reviewed EPUB batch without touching SQLite or Chroma.

Each worker owns a disjoint group of books and writes only its own stage JSON
and translation-cache folders. A later serial ingest consumes those caches.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOKS_KB = ROOT / "books_kb"
sys.path.insert(0, str(BOOKS_KB))
import ingest_text_epub_latam as ingest  # noqa: E402


ALLOWED_ACTIONS = {
    "ingest_without_translation_then_qa",
    "translate_to_latam_then_ingest_then_qa",
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_completed_hashes(report: Path | None) -> set[str]:
    if report is None or not report.exists():
        return set()
    payload = json.loads(report.read_text(encoding="utf-8"))
    return {
        str(row.get("md5"))
        for row in payload.get("results", [])
        if row.get("status") == "ok" and row.get("md5")
    }


def balanced_worker_rows(rows: list[dict], workers: int, worker_id: int) -> list[dict]:
    buckets: list[list[dict]] = [[] for _ in range(workers)]
    totals = [0] * workers
    for row in sorted(rows, key=lambda item: int(item.get("native_words_est") or 0), reverse=True):
        target = min(range(workers), key=lambda index: totals[index])
        buckets[target].append(row)
        totals[target] += int(row.get("native_words_est") or 0)
    return buckets[worker_id]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--worker-id", type=int, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--exclude-report", type=Path)
    parser.add_argument("--min-native-words", type=int, default=500)
    parser.add_argument("--translation-provider", choices=["gemini", "google"], default="gemini")
    parser.add_argument("--allow-google-fallback", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.worker_id < args.workers:
        raise SystemExit("worker-id must be between 0 and workers - 1")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    completed = load_completed_hashes(args.exclude_report)
    candidates = [
        row for row in manifest.get("rows", [])
        if row.get("extension") == ".epub"
        and row.get("duplicate_status") == "new"
        and row.get("recommended_action") in ALLOWED_ACTIONS
        and int(row.get("native_words_est") or 0) >= args.min_native_words
        and row.get("md5") not in completed
    ]
    selected = balanced_worker_rows(candidates, args.workers, args.worker_id)
    stage_path = args.stage_dir / f"worker_{args.worker_id + 1:02d}.json"
    previous = json.loads(stage_path.read_text(encoding="utf-8")) if stage_path.exists() else {"results": []}
    results = [row for row in previous.get("results", []) if row.get("status") == "ok"]
    staged_hashes = {row.get("md5") for row in results}

    for row in selected:
        if row.get("md5") in staged_hashes:
            continue
        try:
            epub = Path(row["path"])
            native_text, extract_stats = ingest.extract_epub_native_text(epub)
            if extract_stats["native_words"] < args.min_native_words:
                raise RuntimeError("EPUB text extraction is below the minimum threshold")
            title = row["title_guess"]
            slug = ingest.pb.slugify(title)
            is_spanish = ingest.looks_like_spanish(native_text)
            blocks = [] if is_spanish else ingest.split_for_translation(native_text)
            if blocks:
                translated_text, audit = ingest.translate_latam(
                    blocks,
                    cache_dir=BOOKS_KB / "docs" / "translation_cache" / slug,
                    allow_google_fallback=args.allow_google_fallback,
                    provider=args.translation_provider,
                )
            else:
                translated_text, audit = native_text, [{"provider": "skipped_source_spanish", "cached": True}]
            translated_text = ingest.clean_translated_text(translated_text)
            flags = ingest.translation_quality_flags(translated_text)
            status = "ok" if not flags else "qa_flags"
            result = {
                "md5": row["md5"],
                "filename": row["filename"],
                "title": title,
                "author": row.get("author_guess", "Desconocido"),
                "language": row.get("language_guess"),
                "native_words": extract_stats["native_words"],
                "translated_words": len(translated_text.split()),
                "translation_blocks": len(blocks),
                "translation_quality_flags": flags,
                "status": status,
                "error": "",
            }
        except Exception as exc:  # noqa: BLE001 - preserve batch progress after a single bad EPUB
            result = {
                "md5": row.get("md5"),
                "filename": row.get("filename"),
                "title": row.get("title_guess"),
                "status": "failed",
                "error": str(exc)[-1200:],
            }
        results.append(result)
        write_json(stage_path, {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "worker_id": args.worker_id,
            "workers": args.workers,
            "results": results,
        })
        print(json.dumps({"worker": args.worker_id + 1, "status": result["status"], "book": result["filename"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
