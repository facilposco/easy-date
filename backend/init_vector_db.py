import json
import sqlite3
from datetime import datetime
from pathlib import Path

import chromadb


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "textgame.db"
CHROMA_PATH = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "natalia_conversations"
BACKUP_DIR = ROOT_DIR / "scratch" / "chroma_backups"


def extract_messages(transcription_json):
    data = json.loads(transcription_json)
    if isinstance(data, dict):
        messages = data.get("messages") or data.get("mensajes") or []
    elif isinstance(data, list):
        messages = data
    else:
        messages = []

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        speaker = (
            message.get("role")
            or message.get("sender")
            or message.get("autor")
            or "unknown"
        )
        text = message.get("content") or message.get("text") or message.get("texto") or ""
        text = str(text).strip()
        if text:
            normalized.append((str(speaker).strip() or "unknown", text))
    return normalized


def build_document(title, profile, messages):
    lines = [
        f"TITLE: {title or ''}",
        f"PROFILE: {profile or ''}",
        "REAL CONVERSATION:",
    ]
    lines.extend(f"{speaker}: {text}" for speaker, text in messages)
    return "\n".join(lines)


def load_conversation_documents():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, post_id, title, girl_profile_type, transcription_json
        FROM reddit_conversations
        WHERE transcription_json IS NOT NULL AND transcription_json != ''
        ORDER BY id
        """
    )
    rows = cur.fetchall()
    conn.close()

    docs = []
    metadatas = []
    ids = []
    errors = []

    for db_id, post_id, title, profile, transcription_json in rows:
        try:
            messages = extract_messages(transcription_json)
            if not messages:
                continue

            docs.append(build_document(title, profile, messages))
            metadatas.append(
                {
                    "db_id": str(db_id),
                    "post_id": str(post_id or ""),
                    "profile": str(profile or ""),
                }
            )
            ids.append(f"reddit_{db_id}")
        except Exception as exc:
            errors.append((db_id, post_id, str(exc)))

    return docs, metadatas, ids, errors


def backup_collection(client):
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{COLLECTION_NAME}_{timestamp}.json"
    data = collection.get(include=["documents", "metadatas"])
    backup_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return backup_path


def init_vector_db():
    print("Initializing ChromaDB...")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")

    CHROMA_PATH.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    backup_path = backup_collection(client)
    if backup_path:
        print(f"Backed up existing collection to {backup_path}")

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    print("Reading Reddit conversations from SQLite...")
    docs, metadatas, ids, errors = load_conversation_documents()
    for db_id, post_id, error in errors:
        print(f"Error processing db_id={db_id}, post_id={post_id}: {error}")

    print(f"Vectorizing {len(docs)} conversations...")
    batch_size = 100
    for start in range(0, len(docs), batch_size):
        end = start + batch_size
        collection.add(
            documents=docs[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
        print(f"Inserted {min(end, len(docs))} / {len(docs)} documents in ChromaDB.")

    print("Vectorization completed.")


if __name__ == "__main__":
    init_vector_db()
