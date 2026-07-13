#!/usr/bin/env python
"""Repair only EPUB translation blocks flagged by semantic QA.

The source text and previous cache value stay in the JSON audit report. SQLite
and Chroma are intentionally untouched; rerun semantic QA before ingesting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOKS_KB = ROOT / "books_kb"
DOCS = ROOT / "docs"
sys.path.insert(0, str(BOOKS_KB))
import ingest_text_epub_latam as ingest  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def cache_path(title: str, index: int, source: str) -> Path:
    digest = hashlib.md5(source.encode("utf-8")).hexdigest()
    return BOOKS_KB / "docs" / "translation_cache" / ingest.pb.slugify(title) / f"block_{index:04d}_{digest}.txt"


def repair_prompt(source: str, previous: str, finding: str) -> str:
    return f"""Corrige la traduccion al espanol latino de un bloque de libro educativo sobre citas.
Devuelve SOLO la traduccion corregida, sin comentarios ni encabezados. Conserva TODO el contenido del original: no resumas, no agregues consejos y no omitas lenguaje adulto si aparece. Mantén marcas, nombres propios y terminos de apps exactamente como corresponda: Tinder, Bumble, Hinge, match, WhatsApp, Instagram y Snapchat no se traducen literalmente. Usa trato de tu natural y consistente cuando el original hable al lector. Corrige gramatica, contexto y ortografia.

HALLAZGO DEL AUDITOR:
{finding}

ORIGINAL:
{source}

TRADUCCION ANTERIOR:
{previous}
"""


def is_quota_error(error: Exception) -> bool:
    text = str(error).lower()
    return "429" in text or "resource_exhausted" in text or "quota exhausted" in text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--semantic-report", type=Path, required=True)
    parser.add_argument("--output-prefix", default="book_semantic_translation_repairs_july10")
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--fallback-model", default="gemini-2.5-flash-lite")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    semantic = read_json(args.semantic_report)
    all_reviewed = [item for item in semantic.get("samples", []) if item.get("status") == "review"]
    output = DOCS / f"{args.output_prefix}.json"
    previous = read_json(output) if output.exists() else {"results": []}
    results: list[dict] = [row for row in previous.get("results", []) if row.get("status") == "repaired"]
    already_repaired = {(str(row.get("book")), int(row.get("block"))) for row in results if row.get("book") and row.get("block")}
    wanted = [item for item in all_reviewed if (str(item.get("book")), int(item.get("block"))) not in already_repaired]
    if args.limit:
        wanted = wanted[: args.limit]
    manifest = read_json(args.manifest)
    by_title = {str(row.get("title_guess")): row for row in manifest.get("rows", [])}
    old_model, old_fallback, old_fail_fast = os.getenv("GEMINI_MODEL"), os.getenv("GEMINI_MODEL_FALLBACKS"), os.getenv("GEMINI_FAIL_FAST_429")
    os.environ["GEMINI_MODEL"] = args.model
    os.environ["GEMINI_MODEL_FALLBACKS"] = args.fallback_model
    os.environ["GEMINI_FAIL_FAST_429"] = "1"
    quota_pending = False
    try:
        translator = ingest.LocalGeminiTranslator()
        for item in wanted:
            title, index = str(item["book"]), int(item["block"])
            row = by_title.get(title)
            if not row:
                results.append({"book": title, "block": index, "status": "failed", "error": "Book not found in manifest."})
                continue
            source_text, _ = ingest.extract_epub_native_text(Path(row["path"]))
            blocks = ingest.split_for_translation(source_text)
            if index < 1 or index > len(blocks):
                results.append({"book": title, "block": index, "status": "failed", "error": "Block is outside current segmentation."})
                continue
            source = blocks[index - 1]
            path = cache_path(title, index, source)
            previous = path.read_text(encoding="utf-8").strip() if path.exists() else ""
            finding = str((item.get("review") or {}).get("rationale") or item.get("error") or "")
            try:
                corrected = ingest.clean_translated_text(translator.generate(repair_prompt(source, previous, finding))).strip()
            except Exception as exc:  # noqa: BLE001 - preserve partial repairs for later retry
                status = "pending_quota" if is_quota_error(exc) else "failed"
                results.append({"book": title, "block": index, "status": status, "error": str(exc)[-500:]})
                quota_pending = status == "pending_quota"
                if quota_pending:
                    break
                continue
            if not corrected:
                results.append({"book": title, "block": index, "status": "failed", "error": "Model returned empty text."})
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(corrected, encoding="utf-8")
            temporary.replace(path)
            results.append({"book": title, "block": index, "status": "repaired", "finding": finding, "source": source, "previous": previous, "corrected": corrected})
            print(json.dumps({"book": title, "block": index, "status": "repaired"}, ensure_ascii=False), flush=True)
    finally:
        for key, value in (("GEMINI_MODEL", old_model), ("GEMINI_MODEL_FALLBACKS", old_fallback), ("GEMINI_FAIL_FAST_429", old_fail_fast)):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    summary = {
        "requested": len(all_reviewed),
        "remaining_before_run": len(wanted),
        "repaired": sum(row["status"] == "repaired" for row in results),
        "failed": sum(row["status"] == "failed" for row in results),
        "pending_quota": sum(row["status"] == "pending_quota" for row in results),
    }
    payload = {"created_at": datetime.now().isoformat(timespec="seconds"), "semantic_report": str(args.semantic_report), "quota_pending": quota_pending, "summary": summary, "results": results}
    write_json(output, payload)
    print(json.dumps({"json": str(output), **summary}, ensure_ascii=False))
    return 3 if quota_pending else (0 if summary["failed"] == 0 else 2)


if __name__ == "__main__":
    raise SystemExit(main())
