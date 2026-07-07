#!/usr/bin/env python
"""Ingest a text-only EPUB into the Natalia books RAG as Spanish LATAM text."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except Exception:  # pragma: no cover - reported at runtime
    google_genai = None
    google_genai_types = None

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional fallback
    GoogleTranslator = None

try:
    from ftfy import fix_text as ftfy_fix_text
except Exception:  # pragma: no cover - optional cleanup
    ftfy_fix_text = None

import process_books as pb


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SOURCE_BOOKS_DIR = BASE_DIR / "source_books"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def next_book_id(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM books").fetchone()[0])


def epub_spine_html_names(epub_path: Path) -> list[str]:
    with ZipFile(epub_path) as zf:
        names = set(zf.namelist())
        try:
            container = ET.fromstring(zf.read("META-INF/container.xml"))
            rootfile = container.find(".//{*}rootfile")
            opf_name = rootfile.attrib["full-path"] if rootfile is not None else ""
            opf = ET.fromstring(zf.read(opf_name))
            opf_dir = str(Path(opf_name).parent).replace("\\", "/")
            if opf_dir == ".":
                opf_dir = ""
            manifest: dict[str, str] = {}
            for item in opf.findall(".//{*}manifest/{*}item"):
                item_id = item.attrib.get("id")
                href = item.attrib.get("href", "")
                media = item.attrib.get("media-type", "")
                if item_id and ("html" in media or href.lower().endswith((".html", ".xhtml", ".htm"))):
                    manifest[item_id] = f"{opf_dir}/{href}".lstrip("/")
            ordered = []
            for itemref in opf.findall(".//{*}spine/{*}itemref"):
                href = manifest.get(itemref.attrib.get("idref", ""))
                if href in names:
                    ordered.append(href)
            if ordered:
                return ordered
        except Exception:
            pass
        return sorted(n for n in names if n.lower().endswith((".html", ".xhtml", ".htm")))


def clean_html_text(raw_html: bytes) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = html.unescape(text)
    return pb.clean_text(text)


def extract_epub_native_text(epub_path: Path) -> tuple[str, dict[str, int]]:
    html_names = epub_spine_html_names(epub_path)
    parts: list[str] = []
    with ZipFile(epub_path) as zf:
        image_count = sum(
            1
            for name in zf.namelist()
            if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"))
        )
        for name in html_names:
            text = clean_html_text(zf.read(name))
            if text:
                parts.append(text)
    native_text = pb.clean_text("\n\n".join(parts))
    stats = {
        "html_docs": len(html_names),
        "images_seen_not_processed": image_count,
        "native_words": len(re.findall(r"\w+", native_text, flags=re.UNICODE)),
    }
    return native_text, stats


def clean_label(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:140]


def epub_doc_records(epub_path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    html_names = epub_spine_html_names(epub_path)
    with ZipFile(epub_path) as zf:
        for index, name in enumerate(html_names, start=1):
            soup = BeautifulSoup(zf.read(name), "html.parser")
            title = ""
            for selector in ["h1", "h2", "h3", "title"]:
                tag = soup.find(selector)
                if tag:
                    title = clean_label(tag.get_text(" "))
                    if title:
                        break
            if not title:
                title = clean_label(soup.get_text(" "))[:80] or f"Documento EPUB {index}"
            records.append({"index": index, "name": name, "title": title})
    return records


def split_for_translation(text: str, max_chars: int = 1800) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        extra = len(paragraph) + 2
        if current and current_len + extra > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += extra
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def load_env_lenient(path: Path) -> None:
    key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key_pattern.match(key):
            continue
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def collect_gemini_keys() -> list[str]:
    load_env_lenient(ROOT_DIR / ".env")
    keys: list[str] = []
    seen: set[str] = set()
    for idx in range(1, 20):
        value = os.getenv(f"GEMINI_API_KEY_{idx}", "").strip()
        if value and value not in seen:
            keys.append(value)
            seen.add(value)
    value = os.getenv("GEMINI_API_KEY", "").strip()
    if value and value not in seen:
        keys.append(value)
    return keys


def gemini_model_candidates() -> list[str]:
    raw = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    raw += "," + os.getenv("GEMINI_MODEL_FALLBACKS", "gemini-2.5-flash-lite,gemini-2.0-flash-lite")
    candidates: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        model = part.strip()
        if model and model not in seen:
            candidates.append(model)
            seen.add(model)
    return candidates


class LocalGeminiTranslator:
    def __init__(self) -> None:
        if google_genai is None:
            raise RuntimeError("google-genai is not installed")
        self.keys = collect_gemini_keys()
        if not self.keys:
            raise RuntimeError("No Gemini API keys found in .env")
        timeout_ms = max(30000, int(os.getenv("GEMINI_TRANSLATION_TIMEOUT_MS", "120000")))
        self.http_options = (
            google_genai_types.HttpOptions(timeout=timeout_ms)
            if google_genai_types is not None
            else {"timeout": timeout_ms}
        )

    def generate(self, prompt: str) -> str:
        last_error: Exception | None = None
        for model_name in gemini_model_candidates():
            for key_index, api_key in enumerate(self.keys, start=1):
                try:
                    client = google_genai.Client(api_key=api_key, http_options=self.http_options)
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    text = getattr(response, "text", None)
                    if not text:
                        raise RuntimeError("Gemini returned empty text")
                    return str(text)
                except Exception as exc:  # noqa: BLE001 - we must rotate on provider errors
                    last_error = exc
                    status = str(exc)
                    print(f"[GeminiTranslate] retry model={model_name} key={key_index}/{len(self.keys)} err={status[:90]}")
                    time.sleep(1.0)
        raise RuntimeError(f"All Gemini translation attempts failed: {last_error}")


def translate_latam(
    blocks: list[str],
    cache_dir: Path,
    allow_google_fallback: bool,
    provider: str,
    sleep_s: float = 0.2,
) -> tuple[str, list[dict[str, object]]]:
    translator = None if provider == "google" else LocalGeminiTranslator()
    google_fallback = GoogleTranslator(source="auto", target="es") if (allow_google_fallback or provider == "google") and GoogleTranslator else None
    translated_blocks: list[str] = []
    audit: list[dict[str, object]] = []
    cache_dir.mkdir(parents=True, exist_ok=True)
    for index, block in enumerate(blocks, start=1):
        digest = hashlib.md5(block.encode("utf-8")).hexdigest()
        cache_path = cache_dir / f"block_{index:04d}_{digest}.txt"
        if cache_path.exists():
            text = cache_path.read_text(encoding="utf-8").strip()
            translated_blocks.append(text)
            audit.append(
                {
                    "block": index,
                    "source_chars": len(block),
                    "translated_chars": len(text),
                    "seconds": 0,
                    "cached": True,
                }
            )
            continue
        prompt = (
            "Traduce fielmente al español latino natural. Corrige ortografía y gramática solo "
            "para que suene bien en LATAM, sin agregar ideas, sin resumir, sin explicar y sin "
            "cambiar el sentido. Mantén listas y párrafos cuando ayuden a la lectura.\n\n"
            f"TEXTO:\n{block}"
        )
        started = time.time()
        provider = "gemini"
        if translator is None:
            if google_fallback is None:
                raise RuntimeError("deep_translator GoogleTranslator is not available")
            provider = "google_translate"
            text = google_fallback.translate(block).strip()
        else:
            try:
                text = translator.generate(prompt).strip()
            except Exception:
                if google_fallback is None:
                    raise
                provider = "google_translate_fallback"
                text = google_fallback.translate(block).strip()
        cache_path.write_text(text, encoding="utf-8")
        elapsed = round(time.time() - started, 2)
        translated_blocks.append(text)
        audit.append(
            {
                "block": index,
                "source_chars": len(block),
                "translated_chars": len(text),
                "seconds": elapsed,
                "provider": provider,
            }
        )
        if sleep_s:
            time.sleep(sleep_s)
    return pb.clean_text("\n\n".join(translated_blocks)), audit


def clean_translated_text(text: str) -> str:
    if ftfy_fix_text is not None:
        for _ in range(3):
            fixed = ftfy_fix_text(text)
            if fixed == text:
                break
            text = fixed
    leakage_patterns = [
        r"Aqu[ií] tienes la traducci[oó]n fiel.*?(?=\n\n|\Z)",
        r"Traducci[oó]n fiel al espa[ñn]ol latino natural.*?(?=\n\n|\Z)",
        r"con correcciones de ortograf[ií]a y gram[aá]tica.*?(?=\n\n|\Z)",
    ]
    for pattern in leakage_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return pb.clean_text(text)


def chroma_upsert(rows: list[dict], collection_name: str, document_key: str) -> None:
    if not rows:
        return
    import chromadb

    client = chromadb.PersistentClient(path=str(pb.CHROMA_DIR))
    collection = client.get_or_create_collection(collection_name)
    for start in range(0, len(rows), 64):
        batch = rows[start : start + 64]
        collection.upsert(
            ids=[row["embedding_id"] for row in batch],
            documents=[row[document_key] for row in batch],
            metadatas=[row["metadata"] for row in batch],
        )


def update_metadata(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM books ORDER BY id").fetchall()
    payload = {
        "updated_at": now_iso(),
        "modelo_embeddings": "Chroma default ONNX 384d para ingestas nuevas; legacy: paraphrase-multilingual-MiniLM-L12-v2",
        "total_libros_unicos": len(rows),
        "total_chunks": sum(row["total_chunks"] or 0 for row in rows),
        "total_conversaciones": sum(row["total_convs"] or 0 for row in rows),
        "libros": [
            {
                "id": row["id"],
                "slug": row["slug"],
                "titulo": row["titulo"],
                "autor": row["autor"],
                "categoria": row["categoria"],
                "archivo_original": row["archivo_original"],
                "total_paginas": row["total_paginas"],
                "total_palabras": row["total_palabras"],
                "total_chunks": row["total_chunks"],
                "total_convs": row["total_convs"],
                "procesado_pct": row["procesado_pct"],
                "hash_md5": row["hash_md5"],
            }
            for row in rows
        ],
    }
    write_json(pb.METADATA_PATH, payload)


def add_column(conn: sqlite3.Connection, table: str, definition: str) -> None:
    name = definition.split()[0]
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if name not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def ensure_chunk_reference_columns(conn: sqlite3.Connection) -> None:
    add_column(conn, "chunks", "epub_doc_index INTEGER")
    add_column(conn, "chunks", "epub_doc_name TEXT")
    add_column(conn, "chunks", "section_title TEXT")
    add_column(conn, "chunks", "page_estimate INTEGER")
    add_column(conn, "chunks", "reference_quality TEXT")
    add_column(conn, "chunks", "reference_updated_at TEXT")
    conn.commit()


def doc_for_chunk(chunk_index: int, total_chunks: int, docs: list[dict[str, object]]) -> dict[str, object]:
    if not docs:
        return {"index": 0, "name": "", "title": ""}
    ratio = (chunk_index + 1) / max(1, total_chunks)
    doc_pos = min(len(docs) - 1, max(0, int((ratio * len(docs)) + 0.999999) - 1))
    return docs[doc_pos]


def apply_chunk_references(
    conn: sqlite3.Connection,
    book_id: int,
    chunks: list[dict[str, object]],
    doc_records: list[dict[str, object]],
    words_per_page: int = 250,
) -> dict[int, dict[str, object]]:
    ensure_chunk_reference_columns(conn)
    references: dict[int, dict[str, object]] = {}
    running_words = 0
    for index, chunk in enumerate(chunks):
        doc = doc_for_chunk(index, len(chunks), doc_records)
        page = max(1, (running_words // words_per_page) + 1)
        running_words += len(re.findall(r"\w+", str(chunk.get("texto", "")), flags=re.UNICODE))
        reference = {
            "epub_doc_index": int(doc.get("index") or 0),
            "epub_doc_name": str(doc.get("name") or ""),
            "section_title": str(doc.get("title") or ""),
            "page_estimate": page,
            "reference_quality": "estimated_from_epub_spine_and_chunk_position",
        }
        references[index] = reference
        conn.execute(
            """
            UPDATE chunks
               SET epub_doc_index = ?,
                   epub_doc_name = ?,
                   section_title = ?,
                   page_estimate = ?,
                   reference_quality = ?,
                   reference_updated_at = ?,
                   capitulo = COALESCE(NULLIF(capitulo, ''), ?),
                   pagina_inicio = COALESCE(pagina_inicio, ?),
                   pagina_fin = COALESCE(pagina_fin, ?)
             WHERE book_id = ? AND chunk_index = ?
            """,
            (
                reference["epub_doc_index"],
                reference["epub_doc_name"],
                reference["section_title"],
                reference["page_estimate"],
                reference["reference_quality"],
                now_iso(),
                reference["section_title"],
                reference["page_estimate"],
                reference["page_estimate"],
                book_id,
                index,
            ),
        )
    conn.commit()
    return references


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest text-only EPUB into Natalia Books KB.")
    parser.add_argument("--epub", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", default="Desconocido")
    parser.add_argument("--translation-chars", type=int, default=1800)
    parser.add_argument("--translation-provider", choices=["gemini", "google"], default="gemini")
    parser.add_argument("--allow-google-fallback", action="store_true")
    parser.add_argument("--skip-chroma", action="store_true")
    args = parser.parse_args()

    pb.ensure_dirs()
    SOURCE_BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    source_target = SOURCE_BOOKS_DIR / args.epub.name
    if not source_target.exists() or file_md5(source_target) != file_md5(args.epub):
        shutil.copy2(args.epub, source_target)

    native_text, extract_stats = extract_epub_native_text(source_target)
    doc_records = epub_doc_records(source_target)
    if extract_stats["native_words"] < 500:
        raise RuntimeError(f"EPUB text extraction looks too small: {extract_stats['native_words']} words")

    translation_blocks = split_for_translation(native_text, max_chars=args.translation_chars)

    with sqlite3.connect(pb.DB_PATH) as conn:
        pb.init_db(conn)
        md5 = file_md5(source_target)
        existing = conn.execute(
            "SELECT id, slug FROM books WHERE hash_md5 = ? OR archivo_original = ?",
            (md5, str(source_target)),
        ).fetchone()
        book_id = int(existing[0]) if existing else next_book_id(conn)
        slug_base = pb.slugify(args.title)
        slug = existing[1] if existing else slug_base
        if not existing:
            while conn.execute("SELECT 1 FROM books WHERE slug = ?", (slug,)).fetchone():
                slug = f"{slug_base}_{book_id}"

        book = pb.BookFile(id=book_id, path=source_target, slug=slug, title=args.title, author=args.author, md5=md5)

        translated_text, translation_audit = translate_latam(
            translation_blocks,
            cache_dir=BASE_DIR / "docs" / "translation_cache" / book.slug,
            allow_google_fallback=args.allow_google_fallback,
            provider=args.translation_provider,
        )
        translated_text = clean_translated_text(translated_text)

        (pb.RAW_DIR / f"libro_{book.id:02d}_original_en.txt").write_text(native_text, encoding="utf-8")
        raw_path = pb.RAW_DIR / f"libro_{book.id:02d}_raw.txt"
        raw_path.write_text(translated_text, encoding="utf-8")
        (pb.RAW_DIR / f"libro_{book.id:02d}_translated_latam.txt").write_text(translated_text, encoding="utf-8")

        chunks = pb.chunk_text(translated_text)
        chunks_path = pb.CHUNKS_DIR / f"libro_{book.id:02d}_chunks.json"
        write_json(chunks_path, chunks)

        conversations: list[dict] = []
        stats = {
            "pages": max(1, extract_stats["html_docs"]),
            "words": len(re.findall(r"\w+", translated_text, flags=re.UNICODE)),
            "images": 0,
        }
        pb.insert_book(conn, book, stats, len(chunks), len(conversations))
        pb.reset_book_rows(conn, book.id)
        chunk_rows = pb.insert_chunks(conn, book, chunks)
        references = apply_chunk_references(conn, book.id, chunks, doc_records)
        for row in chunk_rows:
            row["metadata"].update(references.get(int(row["metadata"]["chunk_index"]), {}))
        conn.execute("DELETE FROM ocr_image_texts WHERE book_id = ?", (book.id,))
        score = pb.write_quality(conn, book.id, stats["words"], 0)
        conn.execute("UPDATE books SET procesado_pct = 100.0 WHERE id = ?", (book.id,))
        conn.commit()

        if not args.skip_chroma:
            chroma_upsert(chunk_rows, "natalia_books_kb", "texto")
        update_metadata(conn)

    report = {
        "book_id": book.id,
        "slug": book.slug,
        "title": book.title,
        "author": book.author,
        "source_epub": str(source_target),
        "original_text_path": str(pb.RAW_DIR / f"libro_{book.id:02d}_original_en.txt"),
        "translated_text_path": str(pb.RAW_DIR / f"libro_{book.id:02d}_translated_latam.txt"),
        "raw_path": str(raw_path),
        "chunks_path": str(chunks_path),
        "native_words": extract_stats["native_words"],
        "translated_words": stats["words"],
        "html_docs": extract_stats["html_docs"],
        "reference_fields": ["epub_doc_index", "epub_doc_name", "section_title", "page_estimate", "reference_quality"],
        "images_seen_not_processed": extract_stats["images_seen_not_processed"],
        "images_processed": 0,
        "translation_blocks": len(translation_blocks),
        "translation_audit": translation_audit,
        "chunks": len(chunks),
        "conversations": 0,
        "quality_score": score,
        "chroma_indexed": not args.skip_chroma,
        "created_at": now_iso(),
    }
    report_path = BASE_DIR / "docs" / f"ingesta_epub_texto_{book.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json(report_path, report)
    print(json.dumps({**report, "translation_audit": f"{len(translation_audit)} blocks"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
