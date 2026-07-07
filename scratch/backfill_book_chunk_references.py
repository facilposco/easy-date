#!/usr/bin/env python
"""Backfill EPUB document/section/page references for book chunks and Chroma metadata."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import chromadb
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = ROOT / "books_kb"
DB_PATH = BOOKS_DIR / "books_index.sqlite"
CHROMA_PATH = BOOKS_DIR / "chroma_books"
DOCS_DIR = ROOT / "docs"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


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


def clean_label(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:140] if value else ""


def epub_spine_html_names(epub_path: Path) -> list[str]:
    import sys

    sys.path.insert(0, str(BOOKS_DIR))
    from ingest_text_epub_latam import epub_spine_html_names as spine_names  # noqa: PLC0415

    return spine_names(epub_path)


def epub_doc_records(epub_path: Path) -> list[dict[str, object]]:
    names = epub_spine_html_names(epub_path)
    records: list[dict[str, object]] = []
    with ZipFile(epub_path) as zf:
        for index, name in enumerate(names, start=1):
            soup = BeautifulSoup(zf.read(name), "html.parser")
            title = ""
            for selector in ["h1", "h2", "h3", "title"]:
                tag = soup.find(selector)
                if tag:
                    title = clean_label(tag.get_text(" "))
                    if title:
                        break
            if not title:
                text = clean_label(soup.get_text(" "))
                title = text[:80] if text else f"Documento EPUB {index}"
            records.append({"index": index, "name": name, "title": title})
    return records


def chunk_page_estimates(chunks: list[sqlite3.Row], words_per_page: int) -> dict[int, int]:
    total_words = 0
    estimates: dict[int, int] = {}
    for row in chunks:
        estimates[int(row["chunk_index"])] = max(1, math.ceil((total_words + 1) / words_per_page))
        total_words += int(row["palabras"] or 0)
    return estimates


def doc_for_chunk(chunk_index: int, total_chunks: int, docs: list[dict[str, object]]) -> dict[str, object]:
    if not docs:
        return {"index": None, "name": "", "title": ""}
    ratio = (chunk_index + 1) / max(1, total_chunks)
    doc_pos = min(len(docs) - 1, max(0, math.ceil(ratio * len(docs)) - 1))
    return docs[doc_pos]


def backfill(book_slug: str, words_per_page: int, apply_chroma: bool) -> dict[str, object]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_chunk_reference_columns(conn)
    book = conn.execute("SELECT * FROM books WHERE slug = ?", (book_slug,)).fetchone()
    if not book:
        raise RuntimeError(f"Book not found: {book_slug}")
    epub_path = Path(book["archivo_original"])
    docs = epub_doc_records(epub_path)
    chunks = conn.execute(
        "SELECT id, chunk_index, texto, palabras, embedding_id, tipo_contenido, temas FROM chunks WHERE book_id = ? ORDER BY chunk_index",
        (book["id"],),
    ).fetchall()
    page_by_chunk = chunk_page_estimates(chunks, words_per_page)

    updated_rows: list[dict[str, object]] = []
    for row in chunks:
        chunk_index = int(row["chunk_index"])
        doc = doc_for_chunk(chunk_index, len(chunks), docs)
        page = page_by_chunk[chunk_index]
        section_title = str(doc.get("title") or "")
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
             WHERE id = ?
            """,
            (
                doc.get("index"),
                doc.get("name"),
                section_title,
                page,
                "estimated_from_epub_spine_and_chunk_position",
                now_iso(),
                section_title,
                page,
                page,
                row["id"],
            ),
        )
        updated_rows.append(
            {
                "embedding_id": row["embedding_id"],
                "document": row["texto"],
                "metadata": {
                    "book_id": int(book["id"]),
                    "book_slug": book["slug"],
                    "libro": book["titulo"],
                    "autor": book["autor"],
                    "chunk_index": chunk_index,
                    "tipo_contenido": row["tipo_contenido"],
                    "temas": row["temas"],
                    "palabras": int(row["palabras"] or 0),
                    "epub_doc_index": int(doc.get("index") or 0),
                    "epub_doc_name": str(doc.get("name") or ""),
                    "section_title": section_title,
                    "page_estimate": page,
                    "reference_quality": "estimated_from_epub_spine_and_chunk_position",
                },
            }
        )
    conn.commit()
    conn.close()

    chroma_updated = 0
    if apply_chroma and updated_rows:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection = client.get_collection("natalia_books_kb")
        for start in range(0, len(updated_rows), 64):
            batch = updated_rows[start : start + 64]
            collection.upsert(
                ids=[str(row["embedding_id"]) for row in batch if row["embedding_id"]],
                documents=[str(row["document"]) for row in batch if row["embedding_id"]],
                metadatas=[row["metadata"] for row in batch if row["embedding_id"]],
            )
            chroma_updated += len([row for row in batch if row["embedding_id"]])

    report = {
        "created_at": now_iso(),
        "book_id": int(book["id"]),
        "book_slug": book["slug"],
        "title": book["titulo"],
        "epub_docs": len(docs),
        "chunks_updated": len(updated_rows),
        "chroma_updated": chroma_updated,
        "words_per_page": words_per_page,
        "reference_quality": "estimated_from_epub_spine_and_chunk_position",
        "sample": [
            {
                "chunk_index": row["metadata"]["chunk_index"],
                "epub_doc_index": row["metadata"]["epub_doc_index"],
                "section_title": row["metadata"]["section_title"],
                "page_estimate": row["metadata"]["page_estimate"],
            }
            for row in updated_rows[:5]
        ],
    }
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / f"book_chunk_references_{book_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill EPUB references for book chunks.")
    parser.add_argument("--book-slug", default="understanding_women_a_simple_guide_to_conquering_women")
    parser.add_argument("--words-per-page", type=int, default=250)
    parser.add_argument("--skip-chroma", action="store_true")
    args = parser.parse_args()
    report = backfill(args.book_slug, args.words_per_page, apply_chroma=not args.skip_chroma)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
