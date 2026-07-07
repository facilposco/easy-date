import argparse
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
IMG_ROOT = ROOT / "imagenes_nuevas"
DOCS_DIR = ROOT / "docs"
KEEP_STATUSES = {"candidate_qa"}
DELETE_STATUSES = {"rejected_low_score", "rejected_negative_outcome", "duplicate_content", "candidate_failed"}


def is_safe_child(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def read_rows():
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT post_id, status, local_paths_json
            FROM reddit_success_scrape_candidates
            WHERE local_paths_json IS NOT NULL AND local_paths_json != ''
            """
        ).fetchall()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reddit_success_scrape_rejected_audit (
                post_id TEXT PRIMARY KEY,
                source_url TEXT,
                title TEXT,
                subreddit TEXT,
                image_urls_json TEXT,
                local_paths_json TEXT,
                ocr_text TEXT,
                ocr_lines_json TEXT,
                objectives_json TEXT,
                score INTEGER,
                status TEXT,
                bytes_downloaded INTEGER,
                discovery_source TEXT,
                category TEXT,
                image_hash TEXT,
                ocr_hash TEXT,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        rows.extend(
            conn.execute(
                """
                SELECT post_id, status, local_paths_json
                FROM reddit_success_scrape_rejected_audit
                WHERE local_paths_json IS NOT NULL AND local_paths_json != ''
                """
            ).fetchall()
        )
        return rows
    finally:
        conn.close()


def candidate_paths(rows):
    keep = set()
    delete = {}
    for post_id, status, paths_json in rows:
        try:
            paths = json.loads(paths_json or "[]")
        except json.JSONDecodeError:
            paths = []
        normalized = []
        for raw in paths:
            path = Path(raw)
            if not path.is_absolute():
                path = ROOT / path
            if is_safe_child(path, IMG_ROOT):
                normalized.append(path.resolve())
        if status in KEEP_STATUSES:
            keep.update(normalized)
        elif status in DELETE_STATUSES:
            delete[post_id] = {"status": status, "paths": normalized}
    return keep, delete


def cleanup(apply=False):
    rows = read_rows()
    keep, delete = candidate_paths(rows)
    report_rows = []
    deleted_files = 0
    deleted_bytes = 0
    deleted_dirs = 0
    skipped_kept = 0

    for post_id, info in sorted(delete.items()):
        post_files = []
        for path in info["paths"]:
            if path in keep:
                skipped_kept += 1
                report_rows.append([post_id, info["status"], str(path), "skipped_kept_candidate", 0])
                continue
            if not path.exists() or not path.is_file():
                report_rows.append([post_id, info["status"], str(path), "missing", 0])
                continue
            size = path.stat().st_size
            if apply:
                path.unlink()
            deleted_files += 1
            deleted_bytes += size
            post_files.append(path)
            report_rows.append([post_id, info["status"], str(path), "deleted" if apply else "would_delete", size])

        post_dir = IMG_ROOT / f"post_{post_id}"
        if is_safe_child(post_dir, IMG_ROOT) and post_dir.exists() and post_dir.is_dir():
            remaining = list(post_dir.iterdir())
            if apply and not remaining:
                post_dir.rmdir()
                deleted_dirs += 1

    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "apply" if apply else "dryrun"
    csv_path = DOCS_DIR / f"reddit_images_cleanup_{mode}_{stamp}.csv"
    summary_path = DOCS_DIR / f"reddit_images_cleanup_{mode}_{stamp}.json"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "status", "path", "action", "bytes"])
        writer.writerows(report_rows)
    summary = {
        "mode": mode,
        "deleted_or_planned_files": deleted_files,
        "deleted_or_planned_bytes": deleted_bytes,
        "deleted_dirs": deleted_dirs,
        "skipped_kept_candidate_files": skipped_kept,
        "csv": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary | {"summary": str(summary_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Delete rejected/duplicate/failed images. Without this flag, only reports.")
    args = parser.parse_args()
    print(json.dumps(cleanup(apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
