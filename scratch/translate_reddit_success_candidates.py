import argparse
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from reddit_success_image_pipeline import DB_PATH, DOCS_DIR, read_env, translate_text, translate_text_latam


def pending_rows(conn, limit):
    sql = """
        SELECT post_id, ocr_text
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
          AND COALESCE(translation_es, '') = ''
          AND COALESCE(ocr_text, '') != ''
        ORDER BY rowid
    """
    if limit:
        sql += " LIMIT ?"
        return conn.execute(sql, (limit,)).fetchall()
    return conn.execute(sql).fetchall()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--provider", choices=["auto", "google"], default="auto")
    parser.add_argument("--report-label", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    DOCS_DIR.mkdir(exist_ok=True)
    env = read_env()
    report_path = DOCS_DIR / f"reddit_success_translation_backfill_{args.report_label}.csv"
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = pending_rows(conn, args.limit)
    translated = 0
    failed = 0

    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["post_id", "status", "chars"])
        writer.writeheader()
        for row in rows:
            text = row["ocr_text"] or ""
            translation = translate_text(text) if args.provider == "google" else translate_text_latam(env, text)
            if translation:
                conn.execute(
                    """
                    UPDATE reddit_success_scrape_candidates
                    SET translation_es = ?, updated_at = ?
                    WHERE post_id = ?
                    """,
                    (translation, datetime.now().isoformat(timespec="seconds"), row["post_id"]),
                )
                conn.commit()
                translated += 1
                writer.writerow({"post_id": row["post_id"], "status": "translated", "chars": len(translation)})
            else:
                failed += 1
                writer.writerow({"post_id": row["post_id"], "status": "failed", "chars": 0})
            f.flush()

    pending = conn.execute(
        """
        SELECT COUNT(*)
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
          AND COALESCE(translation_es, '') = ''
          AND COALESCE(ocr_text, '') != ''
        """
    ).fetchone()[0]
    conn.close()
    print(f"translated={translated} failed={failed} pending={pending} report={report_path}")


if __name__ == "__main__":
    main()
