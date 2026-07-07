import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "textgame.db"
CHROMA_PATH = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "natalia_success_cases"
NEGATIVE_COLLECTION_NAME = "natalia_negative_cases"
BACKUP_DIR = ROOT_DIR / "scratch" / "chroma_backups"


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def parse_objectives(raw: str) -> list[str]:
    try:
        data = json.loads(raw or "[]")
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [clean_text(item) for item in data if clean_text(item)]


def time_markers(text: str) -> list[str]:
    import re

    value = str(text or "")
    patterns = [
        r"\b\d{1,2}:\d{2}\s?(?:AM|PM|a\.m\.|p\.m\.)?\b",
        r"\b(?:today|yesterday|ayer|hoy|lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
        r"\b\d+\s?(?:min|mins|minutes|hour|hours|hora|horas|h)\b",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, value, flags=re.IGNORECASE))
    return [clean_text(item) for item in found if clean_text(item)]


def confidence_for(row: sqlite3.Row) -> tuple[str, list[str]]:
    reasons: list[str] = []
    objectives = parse_objectives(row["objectives_json"])
    score = int(row["score"] or 0)
    ocr_text = clean_text(row["translation_es"] or "")
    source_url = clean_text(row["source_url"] or "")
    local_paths = clean_text(row["local_paths_json"] or "")
    if objectives:
        reasons.append("objetivo_detectado")
    if score >= 8:
        reasons.append("score_alto")
    elif score >= 6:
        reasons.append("score_medio")
    if len(ocr_text.split()) >= 35:
        reasons.append("conversacion_suficiente")
    if local_paths and local_paths != "[]":
        reasons.append("imagen_local")
    if source_url:
        reasons.append("url_original")
    markers = time_markers(ocr_text)
    if markers:
        reasons.append("marcas_tiempo")

    strong = sum(
        1
        for item in [
            bool(objectives),
            score >= 8,
            len(ocr_text.split()) >= 35,
            bool(markers),
            bool(source_url),
        ]
        if item
    )
    if strong >= 4:
        return "alta", reasons
    if strong >= 2:
        return "media", reasons
    return "baja", reasons


def build_document(row: sqlite3.Row, max_translation_chars: int) -> str:
    objectives = parse_objectives(row["objectives_json"])
    confidence, reasons = confidence_for(row)
    markers = time_markers(row["translation_es"] or row["ocr_text"] or "")
    title = clean_text(row["title_es"] or row["title"])
    summary = clean_text(row["summary_es"])
    translation = clean_text(row["translation_es"])[:max_translation_chars]
    return "\n".join(
        part
        for part in [
            "CASO REAL EXITOSO REDDIT",
            f"post_id: {row['post_id']}",
            f"titulo: {title}",
            f"subreddit: {clean_text(row['subreddit'])}",
            f"score_qa: {row['score'] or ''}/10",
            f"objetivos: {', '.join(objectives)}",
            f"confidence: {confidence} ({', '.join(reasons)})",
            f"marcas_tiempo: {', '.join(markers[:8])}",
            f"resumen: {summary}",
            "conversacion_traducida_latam:",
            translation,
        ]
        if clean_text(part)
    )


def load_rows(limit: int | None = None) -> list[sqlite3.Row]:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT post_id, source_url, title, title_es, subreddit, translation_es,
               objectives_json, score, summary_es, status, updated_at,
               ocr_text, ocr_lines_json, local_paths_json
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
          AND translation_es IS NOT NULL
          AND translation_es != ''
        ORDER BY post_id
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def load_negative_rows(limit: int) -> list[sqlite3.Row]:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT post_id, source_url, title, subreddit, ocr_text, ocr_lines_json,
               objectives_json, score, status, error_message, updated_at
        FROM reddit_success_scrape_rejected_audit
        WHERE status IN ('rejected_low_score', 'rejected_negative_outcome')
          AND COALESCE(ocr_text, '') != ''
        ORDER BY updated_at DESC, rowid DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def backup_collection(client: chromadb.PersistentClient) -> Path | None:
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"{COLLECTION_NAME}_{timestamp}.json"
    data = collection.get(include=["documents", "metadatas"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def backup_named_collection(client: chromadb.PersistentClient, collection_name: str) -> Path | None:
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"{collection_name}_{timestamp}.json"
    data = collection.get(include=["documents", "metadatas"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def existing_ids(collection: Any) -> set[str]:
    try:
        data = collection.get(include=[])
    except Exception:
        return set()
    return set(str(item) for item in (data.get("ids") or []))


def index_success_candidates(
    batch_size: int,
    max_translation_chars: int,
    limit: int | None = None,
    incremental: bool = False,
) -> dict[str, Any]:
    rows = load_rows(limit=limit)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    backup_path = None
    if incremental:
        collection = client.get_or_create_collection(COLLECTION_NAME)
        known_ids = existing_ids(collection)
        rows = [row for row in rows if f"success_{row['post_id']}" not in known_ids]
    else:
        backup_path = backup_collection(client)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        collection = client.create_collection(COLLECTION_NAME)

    inserted = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        docs = [build_document(row, max_translation_chars) for row in batch]
        ids = [f"success_{row['post_id']}" for row in batch]
        metadatas = [
            {
                "source_table": "reddit_success_scrape_candidates",
                "post_id": str(row["post_id"]),
                "source_url": str(row["source_url"] or ""),
                "subreddit": str(row["subreddit"] or ""),
                "score": int(row["score"] or 0),
                "objectives": ", ".join(parse_objectives(row["objectives_json"])),
                "confidence": confidence_for(row)[0],
                "confidence_reasons": ", ".join(confidence_for(row)[1]),
                "time_markers_count": len(time_markers(row["translation_es"] or row["ocr_text"] or "")),
                "has_time_markers": bool(time_markers(row["translation_es"] or row["ocr_text"] or "")),
                "updated_at": str(row["updated_at"] or ""),
            }
            for row in batch
        ]
        collection.add(documents=docs, ids=ids, metadatas=metadatas)
        inserted += len(batch)
        print(f"inserted {inserted}/{len(rows)}")

    return {
        "collection": COLLECTION_NAME,
        "rows_loaded": len(rows),
        "inserted": inserted,
        "collection_count": collection.count(),
        "backup_path": str(backup_path) if backup_path else "",
        "chroma_path": str(CHROMA_PATH),
        "incremental": incremental,
    }


def build_negative_document(row: sqlite3.Row, max_chars: int = 2500) -> str:
    objectives = parse_objectives(row["objectives_json"])
    return "\n".join(
        part
        for part in [
            "CASO NEGATIVO / RECHAZADO PARA MAXIMUS",
            f"post_id: {row['post_id']}",
            f"titulo: {clean_text(row['title'])}",
            f"subreddit: {clean_text(row['subreddit'])}",
            f"status: {row['status']}",
            f"score_qa: {row['score'] or ''}/10",
            f"objetivos_detectados: {', '.join(objectives)}",
            f"razon_rechazo: {clean_text(row['error_message'])}",
            "ocr_original:",
            clean_text(row["ocr_text"])[:max_chars],
        ]
        if clean_text(part)
    )


def index_negative_cases(batch_size: int, limit: int) -> dict[str, Any]:
    rows = load_negative_rows(limit=limit)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    backup_path = backup_named_collection(client, NEGATIVE_COLLECTION_NAME)
    try:
        client.delete_collection(NEGATIVE_COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(NEGATIVE_COLLECTION_NAME)
    inserted = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        collection.add(
            documents=[build_negative_document(row) for row in batch],
            ids=[f"negative_{row['post_id']}" for row in batch],
            metadatas=[
                {
                    "source_table": "reddit_success_scrape_rejected_audit",
                    "post_id": str(row["post_id"]),
                    "source_url": str(row["source_url"] or ""),
                    "subreddit": str(row["subreddit"] or ""),
                    "status": str(row["status"] or ""),
                    "score": int(row["score"] or 0),
                    "objectives": ", ".join(parse_objectives(row["objectives_json"])),
                    "updated_at": str(row["updated_at"] or ""),
                }
                for row in batch
            ],
        )
        inserted += len(batch)
        print(f"inserted negative {inserted}/{len(rows)}")
    return {
        "collection": NEGATIVE_COLLECTION_NAME,
        "rows_loaded": len(rows),
        "inserted": inserted,
        "collection_count": collection.count(),
        "backup_path": str(backup_path) if backup_path else "",
        "chroma_path": str(CHROMA_PATH),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-translation-chars", type=int, default=4500)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--negative-limit", type=int, default=1000)
    parser.add_argument("--index-negatives", action="store_true")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    result = index_success_candidates(
        batch_size=max(1, args.batch_size),
        max_translation_chars=max(500, args.max_translation_chars),
        limit=args.limit or None,
        incremental=args.incremental,
    )
    if args.index_negatives:
        result["negative_cases"] = index_negative_cases(
            batch_size=max(1, args.batch_size),
            limit=max(1, args.negative_limit),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.report:
        Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
