import json
import sqlite3
import sys
from pathlib import Path

import chromadb


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "textgame.db"
CHROMA_PATH = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "natalia_conversations"

sys.path.insert(0, str(ROOT_DIR))
from backend.init_vector_db import load_conversation_documents  # noqa: E402


def scalar(cursor, query):
    return cursor.execute(query).fetchone()[0]


def sqlite_counts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    tables = {
        row[0]
        for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }

    counts = {
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "tables": sorted(tables),
    }

    if "reddit_conversations" in tables:
        counts["reddit_conversations"] = scalar(cur, "SELECT COUNT(*) FROM reddit_conversations")
        counts["reddit_conversations_with_transcription_json"] = scalar(
            cur,
            """
            SELECT COUNT(*)
            FROM reddit_conversations
            WHERE transcription_json IS NOT NULL AND transcription_json != ''
            """,
        )

    if "chat_turns" in tables:
        counts["chat_turns"] = scalar(cur, "SELECT COUNT(*) FROM chat_turns")
        counts["chat_turns_with_user_message"] = scalar(
            cur,
            """
            SELECT COUNT(*)
            FROM chat_turns
            WHERE user_message IS NOT NULL AND user_message != ''
            """,
        )

    conn.close()
    return counts


def chroma_counts(expected_ids):
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collections = {}
    target = None

    for collection_ref in client.list_collections():
        name = getattr(collection_ref, "name", str(collection_ref))
        collection = client.get_collection(name)
        count = collection.count()
        collections[name] = count

        if name == COLLECTION_NAME:
            data = collection.get(include=["documents", "metadatas"])
            ids = set(data.get("ids", []))
            target = {
                "count": count,
                "id_matches_expected": len(ids.intersection(expected_ids)),
                "ids_not_expected": len(ids.difference(expected_ids)),
                "expected_ids_missing": len(expected_ids.difference(ids)),
            }

    return {
        "chroma_path": str(CHROMA_PATH),
        "collections": collections,
        "target_collection": COLLECTION_NAME,
        "target": target,
    }


def main():
    docs, metadatas, ids, errors = load_conversation_documents()
    expected_ids = set(ids)
    sqlite_summary = sqlite_counts()
    chroma_summary = chroma_counts(expected_ids)

    summary = {
        "sqlite": sqlite_summary,
        "vectorizable_from_reddit_conversations": {
            "count": len(docs),
            "ids": len(ids),
            "metadatas": len(metadatas),
            "parse_errors": len(errors),
            "sample_errors": errors[:5],
        },
        "chroma": chroma_summary,
        "coherence": {
            "target_count_matches_vectorizable": (
                chroma_summary["target"] is not None
                and chroma_summary["target"]["count"] == len(docs)
            ),
            "backend_collection_only": COLLECTION_NAME,
        },
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
