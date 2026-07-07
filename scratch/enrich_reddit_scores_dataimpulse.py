#!/usr/bin/env python
"""Enrich accepted Reddit success candidates with exact Reddit score.

This is intentionally a post-processing pass. The mass scraper should stay fast
and use search ranking as a cheap score proxy; this script only enriches rows
that already passed OCR/scoring QA.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

from reddit_success_image_pipeline import DB_PATH, DOCS_DIR, fetch_post_score, read_env


DB_LOCK_TIMEOUT = 30


def ensure_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(reddit_success_scrape_candidates)")}
    migrations = {
        "reddit_score": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN reddit_score INTEGER",
        "reddit_score_source": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN reddit_score_source TEXT",
        "reddit_score_checked_at": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN reddit_score_checked_at TEXT",
        "reddit_score_error": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN reddit_score_error TEXT",
    }
    for column, sql in migrations.items():
        if column not in columns:
            conn.execute(sql)
    conn.commit()


def load_targets(limit: int, min_local_score: int) -> list[dict]:
    conn = sqlite3.connect(DB_PATH, timeout=DB_LOCK_TIMEOUT)
    conn.row_factory = sqlite3.Row
    try:
        ensure_columns(conn)
        rows = conn.execute(
            """
            SELECT post_id, source_url, title, score
            FROM reddit_success_scrape_candidates
            WHERE status = 'candidate_qa'
              AND post_id IS NOT NULL
              AND COALESCE(reddit_score_checked_at, '') = ''
              AND COALESCE(score, 0) >= ?
            ORDER BY COALESCE(score, 0) DESC, updated_at DESC
            LIMIT ?
            """,
            (min_local_score, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_row(post_id: str, score: int | None, source: str, error: str = "") -> None:
    conn = sqlite3.connect(DB_PATH, timeout=DB_LOCK_TIMEOUT)
    try:
        ensure_columns(conn)
        conn.execute(
            """
            UPDATE reddit_success_scrape_candidates
            SET reddit_score = ?,
                reddit_score_source = ?,
                reddit_score_checked_at = ?,
                reddit_score_error = ?
            WHERE post_id = ?
            """,
            (score, source, datetime.now().isoformat(timespec="seconds"), error[:500], post_id),
        )
        conn.commit()
    finally:
        conn.close()


def enrich_one(env: dict, target: dict) -> dict:
    session = requests.Session()
    post_id = target["post_id"]
    try:
        score = fetch_post_score(session, env, post_id, allow_decodo=False, allow_dataimpulse=True)
        update_row(post_id, score, "direct_or_dataimpulse")
        return {**target, "reddit_score": score, "source": "direct_or_dataimpulse", "error": ""}
    except Exception as exc:
        update_row(post_id, None, "failed", str(exc))
        return {**target, "reddit_score": None, "source": "failed", "error": str(exc)}
    finally:
        session.close()


def write_report(rows: list[dict], run_label: str) -> Path:
    DOCS_DIR.mkdir(exist_ok=True)
    out = DOCS_DIR / f"reddit_score_enrichment_{run_label}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["post_id", "reddit_score", "source", "local_score", "title", "source_url", "error"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "post_id": row.get("post_id", ""),
                    "reddit_score": row.get("reddit_score", ""),
                    "source": row.get("source", ""),
                    "local_score": row.get("score", ""),
                    "title": row.get("title", ""),
                    "source_url": row.get("source_url", ""),
                    "error": row.get("error", ""),
                }
            )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--min-local-score", type=int, default=6)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--run-label", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    env = read_env()
    targets = load_targets(args.limit, args.min_local_score)
    print(f"targets={len(targets)} db={DB_PATH}", flush=True)
    if not targets:
        return

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for target in targets:
            futures.append(executor.submit(enrich_one, env, target))
            if args.sleep > 0:
                time.sleep(args.sleep)
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            print(
                f"{len(results)}/{len(targets)} {row['post_id']} reddit_score={row.get('reddit_score')} source={row.get('source')}",
                flush=True,
            )

    report = write_report(results, args.run_label)
    ok = sum(1 for row in results if row.get("reddit_score") is not None)
    print(f"done ok={ok} failed={len(results)-ok} report={report}", flush=True)


if __name__ == "__main__":
    main()
