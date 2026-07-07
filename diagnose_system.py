import json
import sqlite3
from pathlib import Path

import chromadb


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "textgame.db"
CHROMA_PATH = ROOT_DIR / "chroma_db"


def sqlite_count(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()[0]


def main():
    report = {
        "sqlite": {"path": str(DB_PATH), "exists": DB_PATH.exists()},
        "chroma": {"path": str(CHROMA_PATH), "exists": CHROMA_PATH.exists(), "collections": {}},
    }

    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        report["sqlite"].update(
            {
                "reddit_conversations": sqlite_count(cur, "SELECT COUNT(*) FROM reddit_conversations"),
                "reddit_conversations_with_transcription": sqlite_count(
                    cur,
                    """
                    SELECT COUNT(*)
                    FROM reddit_conversations
                    WHERE transcription_json IS NOT NULL AND transcription_json != ''
                    """,
                ),
                "chat_turns": sqlite_count(cur, "SELECT COUNT(*) FROM chat_turns"),
                "transcripts": sqlite_count(cur, "SELECT COUNT(*) FROM transcripts"),
            }
        )
        conn.close()

    if CHROMA_PATH.exists():
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        for collection in client.list_collections():
            report["chroma"]["collections"][collection.name] = collection.count()

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
