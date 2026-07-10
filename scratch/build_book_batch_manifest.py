#!/usr/bin/env python
"""Build an auditable manifest before ingesting a batch of books.

The manifest is intentionally conservative: it does not modify the books RAG,
Chroma, or SQLite. It scans candidate files, estimates language/category,
detects duplicates against books_kb/books_index.sqlite, and writes CSV/JSON/HTML
reports in docs/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
BOOKS_DB = ROOT / "books_kb" / "books_index.sqlite"
DOCS = ROOT / "docs"
DEFAULT_INPUT = Path(r"C:\Users\New\Documents\Libros epub")
SUPPORTED_EXTENSIONS = {".epub", ".txt", ".md", ".html", ".htm", ".pdf"}
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "books_kb",
    "docs",
    "scratch",
    "traducidos",
}


@dataclass
class ManifestRow:
    index: int
    path: str
    filename: str
    extension: str
    size_mb: float
    md5: str
    title_guess: str
    author_guess: str
    language_guess: str
    category_guess: str
    native_words_est: int
    html_docs: int
    images_seen: int
    duplicate_status: str
    duplicate_reason: str
    recommended_action: str
    priority: str


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def epub_opf_path(zf: ZipFile) -> str:
    try:
        container = ET.fromstring(zf.read("META-INF/container.xml"))
        rootfile = container.find(".//{*}rootfile")
        if rootfile is not None:
            return rootfile.attrib.get("full-path", "")
    except Exception:
        return ""
    return ""


def epub_metadata(path: Path) -> tuple[str, str, str, int, int, int]:
    title = ""
    author = ""
    sample_parts: list[str] = []
    html_docs = 0
    images_seen = 0
    with ZipFile(path) as zf:
        names = zf.namelist()
        images_seen = sum(1 for name in names if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")))
        opf_name = epub_opf_path(zf)
        if opf_name:
            try:
                opf = ET.fromstring(zf.read(opf_name))
                title_node = opf.find(".//{*}title")
                author_node = opf.find(".//{*}creator")
                title = clean_text(title_node.text or "") if title_node is not None else ""
                author = clean_text(author_node.text or "") if author_node is not None else ""
            except Exception:
                pass
        html_names = [name for name in names if name.lower().endswith((".html", ".xhtml", ".htm"))]
        html_docs = len(html_names)
        for name in html_names[:12]:
            try:
                sample_parts.append(clean_text(zf.read(name).decode("utf-8", errors="ignore")))
            except Exception:
                continue
    sample = clean_text(" ".join(sample_parts))[:50000]
    words = len(re.findall(r"\w+", sample, flags=re.UNICODE))
    return title, author, sample, words, html_docs, images_seen


def read_sample(path: Path) -> tuple[str, str, str, int, int, int]:
    if path.suffix.lower() == ".epub":
        return epub_metadata(path)
    if path.suffix.lower() in {".txt", ".md", ".html", ".htm"}:
        text = clean_text(path.read_text(encoding="utf-8", errors="ignore"))[:50000]
        return "", "", text, len(re.findall(r"\w+", text, flags=re.UNICODE)), 1, 0
    return "", "", "", 0, 0, 0


def language_guess(text: str, filename: str) -> str:
    sample = f" {text[:30000].lower()} {filename.lower()} "
    scores = {
        "es": sum(sample.count(token) for token in [" que ", " de ", " la ", " el ", " para ", " mujeres", " atraccion", " cita"]),
        "en": sum(sample.count(token) for token in [" the ", " and ", " women", " attraction", " dating", " conversation"]),
        "pt": sum(sample.count(token) for token in [" que ", " para ", " mulheres", " atracao", " encontro", " voce"]),
        "fr": sum(sample.count(token) for token in [" les ", " des ", " femme", " attraction", " rendez vous"]),
        "de": sum(sample.count(token) for token in [" der ", " die ", " frauen", " verabredung", " anziehung"]),
        "it": sum(sample.count(token) for token in [" che ", " donne", " attrazione", " appuntamento"]),
    }
    best, value = max(scores.items(), key=lambda item: item[1])
    return best if value > 0 else "unknown"


def category_guess(text: str, filename: str) -> str:
    sample = normalize(f"{filename} {text[:30000]}")
    if any(term in sample for term in ["text game", "message game", "tinder", "bumble", "whatsapp", "sms", "chat"]):
        return "text_game"
    if any(term in sample for term in ["female psychology", "psicologia femenina", "cerebro femenino", "women psychology", "mujeres"]):
        return "psicologia_femenina"
    if any(term in sample for term in ["seduction", "seduccion", "attraction", "atraccion", "pickup", "pick up"]):
        return "seduccion_general"
    if any(term in sample for term in ["communication", "comunicacion", "conversation", "conversacion"]):
        return "comunicacion"
    return "pendiente_revision"


def load_existing_books() -> tuple[set[str], set[str], dict[str, str]]:
    hashes: set[str] = set()
    titles: set[str] = set()
    source_paths: dict[str, str] = {}
    if not BOOKS_DB.exists():
        return hashes, titles, source_paths
    with sqlite3.connect(BOOKS_DB) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute("SELECT titulo, autor, hash_md5, archivo_original FROM books"):
            if row["hash_md5"]:
                hashes.add(str(row["hash_md5"]).lower())
            titles.add(normalize(f"{row['titulo']} {row['autor']}"))
            if row["archivo_original"]:
                source_paths[str(Path(row["archivo_original"]).resolve()).lower()] = str(row["hash_md5"] or "").lower()
    return hashes, titles, source_paths


def iter_files(inputs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        if item.is_dir():
            files.extend(
                path
                for path in item.rglob("*")
                if path.is_file()
                and path.suffix.lower() in SUPPORTED_EXTENSIONS
                and not any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in path.relative_to(item).parts[:-1])
            )
        elif item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(item)
    return sorted(dict.fromkeys(files), key=lambda p: str(p).lower())


def duplicate_check(
    path: Path,
    md5: str,
    title: str,
    author: str,
    existing_hashes: set[str],
    existing_titles: set[str],
    source_paths: dict[str, str],
) -> tuple[str, str]:
    if md5.lower() in existing_hashes:
        return "duplicate", "hash_md5 already exists in books_index.sqlite"
    source_hash = source_paths.get(str(path.resolve()).lower())
    if source_hash is not None:
        return "possible_duplicate", "same original source path exists in books_index.sqlite with a different hash"
    title_key = normalize(f"{title} {author}")
    if title_key and title_key in existing_titles:
        return "possible_duplicate", "normalized title/author already exists"
    return "new", ""


def action_for(row: ManifestRow) -> tuple[str, str]:
    if row.duplicate_status == "duplicate":
        return "skip", "low"
    if row.duplicate_status == "possible_duplicate":
        return "manual_review_before_ingest", "medium"
    if row.extension == ".pdf":
        return "manual_review_pdf_or_convert_to_epub_text", "medium"
    if row.extension == ".epub" and row.language_guess == "es":
        return "ingest_without_translation_then_qa", "high"
    if row.extension == ".epub" and row.language_guess in {"en", "pt", "fr", "de", "it"}:
        return "translate_to_latam_then_ingest_then_qa", "high"
    return "manual_review_language_category", "medium"


def build_manifest(inputs: list[Path]) -> list[ManifestRow]:
    existing_hashes, existing_titles, source_paths = load_existing_books()
    rows: list[ManifestRow] = []
    for index, path in enumerate(iter_files(inputs), start=1):
        md5 = file_md5(path)
        title, author, sample, words, html_docs, images_seen = read_sample(path)
        title = title or path.stem
        language = language_guess(sample, path.name)
        category = category_guess(sample, path.name)
        duplicate_status, duplicate_reason = duplicate_check(
            path, md5, title, author, existing_hashes, existing_titles, source_paths
        )
        row = ManifestRow(
            index=index,
            path=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            size_mb=round(path.stat().st_size / (1024 * 1024), 3),
            md5=md5,
            title_guess=title,
            author_guess=author or "Desconocido",
            language_guess=language,
            category_guess=category,
            native_words_est=words,
            html_docs=html_docs,
            images_seen=images_seen,
            duplicate_status=duplicate_status,
            duplicate_reason=duplicate_reason,
            recommended_action="",
            priority="",
        )
        row.recommended_action, row.priority = action_for(row)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[ManifestRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()) if rows else list(ManifestRow.__annotations__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_html(path: Path, rows: list[ManifestRow]) -> None:
    trs = []
    for row in rows:
        data = asdict(row)
        trs.append(
            "<tr>"
            + "".join(f"<td>{html.escape(str(data[key]))}</td>" for key in [
                "index",
                "filename",
                "size_mb",
                "language_guess",
                "category_guess",
                "native_words_est",
                "images_seen",
                "duplicate_status",
                "recommended_action",
                "priority",
            ])
            + "</tr>"
        )
    doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Manifiesto lote libros Natalia</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #172026; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee4; padding: 7px; vertical-align: top; }}
    th {{ background: #f4f7f8; text-align: left; }}
    .note {{ border-left: 4px solid #0f766e; padding-left: 10px; color: #5b6770; }}
  </style>
</head>
<body>
  <h1>Manifiesto lote libros Natalia</h1>
  <p class="note">Este reporte no ingesta ni modifica el RAG. Sirve para revisar duplicados, idioma, categoria y siguiente accion antes de procesar libros nuevos.</p>
  <table>
    <thead><tr><th>#</th><th>Archivo</th><th>MB</th><th>Idioma</th><th>Categoria</th><th>Palabras est.</th><th>Imagenes</th><th>Duplicado</th><th>Accion recomendada</th><th>Prioridad</th></tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", help="Files or folders to scan. Defaults to the user's EPUB folder.")
    parser.add_argument("--prefix", default=None, help="Output prefix under docs/.")
    args = parser.parse_args()
    inputs = [Path(item) for item in args.inputs] if args.inputs else [DEFAULT_INPUT]
    rows = build_manifest(inputs)
    stamp = now_stamp()
    prefix = args.prefix or f"book_batch_manifest_{stamp}"
    DOCS.mkdir(parents=True, exist_ok=True)
    json_path = DOCS / f"{prefix}.json"
    csv_path = DOCS / f"{prefix}.csv"
    html_path = DOCS / f"{prefix}.html"
    payload = {"generated_at": stamp, "inputs": [str(p) for p in inputs], "count": len(rows), "rows": [asdict(row) for row in rows]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(csv_path, rows)
    write_html(html_path, rows)
    print(json.dumps({"ok": True, "count": len(rows), "json": str(json_path), "csv": str(csv_path), "html": str(html_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
