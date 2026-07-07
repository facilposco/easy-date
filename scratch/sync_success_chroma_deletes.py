import argparse
import csv
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
DOCS_DIR = ROOT_DIR / "docs"


def candidate_post_ids() -> set[str]:
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT post_id
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
        """
    ).fetchall()
    conn.close()
    return {str(row[0]) for row in rows if row and row[0]}


def chroma_success_ids() -> list[dict[str, Any]]:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(COLLECTION_NAME)
    data = collection.get(include=["metadatas"])
    ids = data.get("ids") or []
    metadatas = data.get("metadatas") or []
    rows: list[dict[str, Any]] = []
    for index, chroma_id in enumerate(ids):
        meta = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        post_id = str(meta.get("post_id") or str(chroma_id).replace("success_", "", 1))
        rows.append({"chroma_id": str(chroma_id), "post_id": post_id})
    return rows


def write_reports(rows: list[dict[str, Any]], apply: bool) -> dict[str, str]:
    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = DOCS_DIR / f"success_chroma_orphans_{stamp}.csv"
    json_path = DOCS_DIR / f"success_chroma_orphans_{stamp}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["chroma_id", "post_id", "action"])
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "apply": apply,
        "orphans": len(rows),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": str(csv_path), "json": str(json_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect or delete orphan success embeddings in Chroma.")
    parser.add_argument("--apply", action="store_true", help="Delete orphan embeddings from Chroma.")
    args = parser.parse_args()

    valid_posts = candidate_post_ids()
    rows = chroma_success_ids()
    orphans = [
        {**row, "action": "deleted" if args.apply else "dry_run"}
        for row in rows
        if row["post_id"] not in valid_posts
    ]

    if args.apply and orphans:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection = client.get_collection(COLLECTION_NAME)
        collection.delete(ids=[row["chroma_id"] for row in orphans])

    reports = write_reports(orphans, args.apply)
    result = {
        "collection": COLLECTION_NAME,
        "valid_candidate_qa": len(valid_posts),
        "chroma_documents_checked": len(rows),
        "orphans": len(orphans),
        "apply": args.apply,
        "reports": reports,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
