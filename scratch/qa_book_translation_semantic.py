#!/usr/bin/env python
"""Audit sampled EPUB translations for fidelity and Spanish-LATAM quality.

This is a post-translation gate: it never edits SQLite, Chroma, originals, or
translations. It samples cached source/translation block pairs reproducibly and
asks a stronger Gemini model to identify meaning-changing omissions or additions.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import random
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOKS_KB = ROOT / "books_kb"
DOCS = ROOT / "docs"
sys.path.insert(0, str(BOOKS_KB))
import ingest_text_epub_latam as ingest  # noqa: E402


PRIORITY_TERMS = (
    "tinder", "bumble", "hinge", "whatsapp", "instagram", "snapchat", "message",
    "text", "date", "cita", "dialogue", "conversation", "example", "consent",
    "sexual", "manipul", "women", "woman", "mujer", "mujeres",
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stage_results(stage_dirs: list[Path]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for stage_dir in stage_dirs:
        for path in sorted(stage_dir.glob("worker_*.json")):
            for row in load_json(path).get("results", []):
                if row.get("md5"):
                    rows[str(row["md5"])] = row
    return rows


def cached_translation(title: str, index: int, source: str) -> str | None:
    digest = hashlib.md5(source.encode("utf-8")).hexdigest()
    path = BOOKS_KB / "docs" / "translation_cache" / ingest.pb.slugify(title) / f"block_{index:04d}_{digest}.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def sampled_indices(blocks: list[str], sample_size: int, seed: str) -> list[int]:
    ranked = [
        index
        for index, block in enumerate(blocks)
        if any(term in block.lower() for term in PRIORITY_TERMS)
    ]
    rng = random.Random(seed)
    remaining = [index for index in range(len(blocks)) if index not in ranked]
    rng.shuffle(ranked)
    rng.shuffle(remaining)
    return (ranked + remaining)[:sample_size]


def parse_json_response(text: str) -> dict:
    clean = text.strip().replace("```json", "").replace("```", "").strip()
    start, end = clean.find("{"), clean.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Reviewer did not return JSON")
    return json.loads(clean[start : end + 1])


def review_book_pairs(translator: ingest.LocalGeminiTranslator, pairs: list[dict]) -> dict[int, dict]:
    rendered = "\n\n".join(
        f"BLOQUE {pair['block']}\nORIGINAL:\n{pair['source']}\n\nTRADUCCION:\n{pair['translation']}"
        for pair in pairs
    )
    prompt = f"""Audita traducciones para un sistema educativo de conversaciones.
Compara cada original y traduccion sin reescribirlos. Evalua fidelidad semantica y espanol latino.
Devuelve SOLO JSON valido con la forma exacta:
{{"reviews":[{{"block":numero,"fidelity_1_10":numero,"latam_1_10":numero,"omission":"","addition":"","terminology_issue":"","verdict":"PASS o REVIEW","rationale":"maximo 35 palabras"}}]}}
Incluye una entrada por cada bloque. Marca REVIEW si cambia el sentido, omite algo relevante,
agrega una idea o el tono latino es poco natural. Conserva nombres propios, marcas y terminos
de apps como Tinder, Bumble, Hinge, match, WhatsApp e Instagram.

{rendered}"""
    payload = parse_json_response(translator.generate(prompt))
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("Reviewer did not return a reviews array")
    return {int(review["block"]): review for review in reviews if isinstance(review, dict) and "block" in review}


def render_html(path: Path, payload: dict) -> None:
    rows = []
    for item in payload["samples"]:
        result = item.get("review", {})
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['book'])}</td><td>{item['block']}</td>"
            f"<td>{html.escape(item['status'])}</td><td>{html.escape(str(result.get('fidelity_1_10', '')))}</td>"
            f"<td>{html.escape(str(result.get('latam_1_10', '')))}</td>"
            f"<td>{html.escape(str(result.get('rationale', item.get('error', ''))))}</td>"
            "</tr>"
        )
    document = f"""<!doctype html><html lang=\"es\"><meta charset=\"utf-8\"><title>QA semantico de traducciones EPUB</title>
<style>body{{font-family:Arial;margin:24px;color:#172026}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d8dee4;padding:7px;vertical-align:top}}th{{background:#f4f7f8;text-align:left}}</style>
<h1>QA semantico de traducciones EPUB</h1><p>Muestra reproducible: {payload['sample_ratio']:.0%}. Modelo auditor: {html.escape(payload['model'])}. No modifica el RAG.</p>
<pre>{html.escape(json.dumps(payload['summary'], ensure_ascii=False, indent=2))}</pre>
<table><thead><tr><th>Libro</th><th>Bloque</th><th>Estado</th><th>Fidelidad</th><th>LATAM</th><th>Hallazgo</th></tr></thead><tbody>{''.join(rows)}</tbody></table></html>"""
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--stage-dir",
        type=Path,
        action="append",
        required=True,
        help="Stage directory to include; repeat to include a focused repair stage.",
    )
    parser.add_argument("--sample-ratio", type=float, default=0.12)
    parser.add_argument("--min-samples", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=12)
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--fallback-model", default="gemini-2.5-flash-lite")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-prefix", default=None)
    args = parser.parse_args()
    if not 0 < args.sample_ratio <= 1:
        raise SystemExit("sample-ratio must be between 0 and 1")

    manifest = load_json(args.manifest)
    staged = stage_results(args.stage_dir)
    old_model, old_fallback = os.getenv("GEMINI_MODEL"), os.getenv("GEMINI_MODEL_FALLBACKS")
    old_fail_fast = os.getenv("GEMINI_FAIL_FAST_429")
    os.environ["GEMINI_MODEL"] = args.model
    os.environ["GEMINI_MODEL_FALLBACKS"] = args.fallback_model
    # A semantic gate must stop at the first quota outage instead of burning all keys.
    os.environ["GEMINI_FAIL_FAST_429"] = "1"
    reviewer = None if args.dry_run else ingest.LocalGeminiTranslator()
    samples: list[dict] = []
    books: list[dict] = []
    quota_pending = False
    quota_error = ""
    try:
        for row in manifest.get("rows", []):
            staged_row = staged.get(str(row.get("md5")))
            if not staged_row or staged_row.get("status") != "ok":
                continue
            epub = Path(row["path"])
            native_text, _ = ingest.extract_epub_native_text(epub)
            if ingest.looks_like_spanish(native_text):
                books.append({"book": row["title_guess"], "status": "skipped_source_spanish", "samples": 0})
                continue
            blocks = ingest.split_for_translation(native_text)
            sample_count = min(args.max_samples, max(args.min_samples, math.ceil(len(blocks) * args.sample_ratio)))
            indices = sampled_indices(blocks, sample_count, str(row["md5"]))
            book_status = "pass"
            book_items: list[dict] = []
            pairs: list[dict] = []
            for zero_index in indices:
                source = blocks[zero_index]
                translation = cached_translation(row["title_guess"], zero_index + 1, source)
                item = {"book": row["title_guess"], "block": zero_index + 1, "status": "pass"}
                if not translation:
                    item.update({"status": "review", "error": "Missing cached translation block"})
                    book_status = "review"
                elif args.dry_run:
                    item["review"] = {"verdict": "DRY_RUN"}
                else:
                    pairs.append({"block": zero_index + 1, "source": source, "translation": translation})
                book_items.append(item)
            if pairs and not args.dry_run:
                try:
                    reviews = review_book_pairs(reviewer, pairs)
                    for item in book_items:
                        if item["block"] not in reviews:
                            item.update({"status": "review", "error": "Reviewer omitted this block."})
                            book_status = "review"
                            continue
                        review = reviews[item["block"]]
                        item["review"] = review
                        if review.get("verdict") != "PASS" or float(review.get("fidelity_1_10", 0)) < 8 or float(review.get("latam_1_10", 0)) < 8:
                            item["status"] = "review"
                            book_status = "review"
                except Exception as exc:  # noqa: BLE001 - preserve a quota gate without creating false reviews
                    error = str(exc)
                    if "429" in error or "RESOURCE_EXHAUSTED" in error or "quota exhausted" in error.lower():
                        quota_pending = True
                        quota_error = error[-500:]
                        book_status = "pending_quota"
                        for item in book_items:
                            if item["block"] in {pair["block"] for pair in pairs}:
                                item.update({"status": "pending_quota", "error": quota_error})
                    else:
                        book_status = "review"
                        for item in book_items:
                            if item["block"] in {pair["block"] for pair in pairs}:
                                item.update({"status": "review", "error": error[-500:]})
            samples.extend(book_items)
            books.append({"book": row["title_guess"], "status": book_status, "samples": len(indices)})
            print(json.dumps({"book": row["title_guess"], "status": book_status}, ensure_ascii=False), flush=True)
            if quota_pending:
                break
    finally:
        if old_model is None:
            os.environ.pop("GEMINI_MODEL", None)
        else:
            os.environ["GEMINI_MODEL"] = old_model
        if old_fallback is None:
            os.environ.pop("GEMINI_MODEL_FALLBACKS", None)
        else:
            os.environ["GEMINI_MODEL_FALLBACKS"] = old_fallback
        if old_fail_fast is None:
            os.environ.pop("GEMINI_FAIL_FAST_429", None)
        else:
            os.environ["GEMINI_FAIL_FAST_429"] = old_fail_fast

    summary = {
        "books": len(books),
        "books_pass": sum(book["status"] == "pass" for book in books),
        "books_review": sum(book["status"] == "review" for book in books),
        "books_pending_quota": sum(book["status"] == "pending_quota" for book in books),
        "books_source_spanish": sum(book["status"] == "skipped_source_spanish" for book in books),
        "samples": len(samples),
        "samples_pass": sum(sample["status"] == "pass" for sample in samples),
        "samples_review": sum(sample["status"] == "review" for sample in samples),
        "samples_pending_quota": sum(sample["status"] == "pending_quota" for sample in samples),
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = args.output_prefix or f"book_semantic_qa_{stamp}"
    json_path, html_path = DOCS / f"{prefix}.json", DOCS / f"{prefix}.html"
    payload = {"created_at": datetime.now().isoformat(timespec="seconds"), "model": args.model, "sample_ratio": args.sample_ratio, "dry_run": args.dry_run, "quota_pending": quota_pending, "quota_error": quota_error, "summary": summary, "books": books, "samples": samples}
    write_json(json_path, payload)
    render_html(html_path, payload)
    print(json.dumps({"json": str(json_path), "html": str(html_path), **summary}, ensure_ascii=False))
    if quota_pending:
        return 3
    return 0 if summary["books_review"] == 0 and summary["samples_review"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
