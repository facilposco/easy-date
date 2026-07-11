#!/usr/bin/env python
"""Run deterministic translation QA over staged Easy Date EPUB books.

This preflight checks every available source/translation pair without calling an
LLM. It complements, but does not replace, the semantic Gemini audit.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOKS_KB = ROOT / "books_kb"
DOCS = ROOT / "docs"
sys.path.insert(0, str(BOOKS_KB))
import ingest_text_epub_latam as ingest  # noqa: E402


TECHNICAL_MARKERS = ("[ocr_image", "source=", "translation_audit", "<script")
SPANISH_MARKERS = (" el ", " la ", " de ", " que ", " para ", " con ", " una ", " los ", " las ")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def staged_hashes(stage_dirs: list[Path]) -> set[str]:
    hashes: set[str] = set()
    for stage_dir in stage_dirs:
        for path in stage_dir.glob("worker_*.json"):
            for row in load_json(path).get("results", []):
                if row.get("status") == "ok" and row.get("md5"):
                    hashes.add(str(row["md5"]))
    return hashes


def cached_translation(title: str, index: int, source: str) -> str | None:
    digest = hashlib.md5(source.encode("utf-8")).hexdigest()
    path = BOOKS_KB / "docs" / "translation_cache" / ingest.pb.slugify(title) / f"block_{index:04d}_{digest}.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def block_flags(source: str, translated: str | None) -> list[str]:
    if not translated:
        return ["missing_translation"]
    flags: list[str] = []
    lower = f" {translated.lower()} "
    if any(marker in translated for marker in ("Ãƒ", "Ã¢â‚¬", "Ã‚")):
        flags.append("mojibake")
    if any(marker in lower and marker not in source.lower() for marker in TECHNICAL_MARKERS):
        flags.append("technical_marker")
    ratio = len(translated) / max(1, len(source))
    if ratio < 0.35 or ratio > 1.9:
        flags.append("length_ratio_anomaly")
    source_numbers = set(re.findall(r"\b\d+(?:[.,:]\d+)?\b", source))
    translated_numbers = set(re.findall(r"\b\d+(?:[.,:]\d+)?\b", translated))
    if source_numbers - translated_numbers:
        flags.append("number_localized_or_missing")
    if len(translated) > 120 and sum(lower.count(marker) for marker in SPANISH_MARKERS) < 2:
        flags.append("spanish_signal_low")
    return flags


def render_html(path: Path, payload: dict) -> None:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['book'])}</td><td>{item['blocks']}</td><td>{item['flagged_blocks']}</td>"
        f"<td>{html.escape(', '.join(item['flag_types']) or 'OK')}</td><td>{html.escape(item['status'])}</td>"
        "</tr>"
        for item in payload["books"]
    )
    path.write_text(
        f"<!doctype html><html lang=\"es\"><meta charset=\"utf-8\"><title>QA local de traducciones EPUB</title>"
        "<style>body{font-family:Arial;margin:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #d8dee4;padding:7px;text-align:left}th{background:#f4f7f8}</style>"
        "<h1>QA local de traducciones EPUB</h1><p>Preflight determinista: no reemplaza la auditoría semántica con Gemini.</p>"
        f"<pre>{html.escape(json.dumps(payload['summary'], ensure_ascii=False, indent=2))}</pre>"
        f"<table><thead><tr><th>Libro</th><th>Bloques</th><th>Con flags</th><th>Tipos</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table></html>",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--stage-dir",
        type=Path,
        action="append",
        required=True,
        help="Stage directory to include; repeat to combine a repair stage with the original stage.",
    )
    parser.add_argument("--output-prefix", default=None)
    args = parser.parse_args()
    staged = staged_hashes(args.stage_dir)
    books: list[dict] = []
    for row in load_json(args.manifest).get("rows", []):
        if str(row.get("md5")) not in staged:
            continue
        native, _ = ingest.extract_epub_native_text(Path(row["path"]))
        if ingest.looks_like_spanish(native):
            books.append({"book": row["title_guess"], "blocks": 0, "flagged_blocks": 0, "flag_types": [], "status": "source_spanish"})
            continue
        flagged: list[str] = []
        for index, source in enumerate(ingest.split_for_translation(native), start=1):
            flags = block_flags(source, cached_translation(row["title_guess"], index, source))
            flagged.extend(flags)
        blocking = {"missing_translation", "mojibake", "technical_marker", "length_ratio_anomaly"}
        books.append({
            "book": row["title_guess"],
            "blocks": len(ingest.split_for_translation(native)),
            "flagged_blocks": len(flagged),
            "flag_types": sorted(set(flagged)),
            "status": "review" if blocking.intersection(flagged) else "pass",
        })
    summary = {
        "books": len(books),
        "pass": sum(book["status"] == "pass" for book in books),
        "review": sum(book["status"] == "review" for book in books),
        "source_spanish": sum(book["status"] == "source_spanish" for book in books),
        "flagged_blocks": sum(book["flagged_blocks"] for book in books),
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = args.output_prefix or f"book_translation_local_qa_{stamp}"
    payload = {"created_at": datetime.now().isoformat(timespec="seconds"), "summary": summary, "books": books}
    json_path, html_path = DOCS / f"{prefix}.json", DOCS / f"{prefix}.html"
    write_json(json_path, payload)
    render_html(html_path, payload)
    print(json.dumps({"json": str(json_path), "html": str(html_path), **summary}, ensure_ascii=False))
    return 0 if summary["review"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
