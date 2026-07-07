import argparse
import csv
import html
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from reddit_success_image_pipeline import (  # noqa: E402
    classify_case,
    detect_objectives,
    save_candidate,
    score_case,
    title_and_summary_es,
)
from reddit_success_parallel_pipeline import (  # noqa: E402
    has_app_context,
    has_chat_evidence,
    has_failure_context,
    has_verified_outcome,
    looks_like_non_chat_screen,
    looks_like_profile_screen,
    title_claims_success,
)


DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"
SPAM_TERMS = [
    "bitcoin",
    "crypto",
    "hacker",
    "recover my",
    "lost account",
    "lost bitcoin",
    "telegram:",
    "prohacker",
    "deleted files",
    "call logs",
    "control devices",
    "remote",
    "gmaildotcom",
]
REMINE_NEGATIVE_TERMS = [
    "no ghosting",
    "if/when",
    "if when",
    "hard not to when i'm subscribed",
    "subscribed to r/",
    "big mistake",
    "niceguys",
    "message prompts",
    "phone number ensued",
    "didn't feel the chemistry",
    "didnt feel the chemistry",
    "didn't feel a spark",
    "didnt feel a spark",
    "as friends",
    "busy tonight",
    "not sure how to respond",
    "starttheconvowit",
    "tap to shuffle",
    "get read receipts",
]


def parse_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def has_spam_context(row):
    hay = " ".join([row["title"] or "", row["ocr_text"] or "", row["source_url"] or ""]).lower()
    return any(term in hay for term in SPAM_TERMS)


def has_remine_negative_context(row):
    hay = " ".join([row["title"] or "", row["ocr_text"] or ""]).lower()
    return any(term in hay for term in REMINE_NEGATIVE_TERMS)


def image_paths_ok(paths):
    return bool(paths) and all(Path(path).exists() for path in paths if path)


def evaluate(row):
    ocr_text = row["ocr_text"] or ""
    title = row["title"] or ""
    subreddit = row["subreddit"] or ""
    entry = {"title": title, "url": row["source_url"] or ""}
    paths = parse_json(row["local_paths_json"], [])
    ocr_lines = parse_json(row["ocr_lines_json"], [])
    objectives = detect_objectives(title, ocr_text)
    score = score_case(title, ocr_text, objectives, len(ocr_lines))

    if not ocr_text.strip():
        return False, "sin_ocr", objectives, score, paths, ocr_lines
    if not image_paths_ok(paths):
        return False, "imagen_faltante", objectives, score, paths, ocr_lines
    if has_spam_context(row):
        return False, "spam_no_dating", objectives, score, paths, ocr_lines
    if has_remine_negative_context(row):
        return False, "negativo_remine", objectives, score, paths, ocr_lines
    if has_failure_context(entry, ocr_text):
        return False, "contexto_fracaso", objectives, score, paths, ocr_lines
    if looks_like_non_chat_screen(ocr_text) or looks_like_profile_screen(ocr_text):
        return False, "perfil_o_pantalla_no_chat", objectives, score, paths, ocr_lines
    if not has_app_context(entry, subreddit, ocr_text):
        return False, "sin_contexto_app_citas", objectives, score, paths, ocr_lines
    if not has_chat_evidence(ocr_text):
        return False, "sin_evidencia_chat", objectives, score, paths, ocr_lines
    if not (has_verified_outcome(objectives, ocr_text) or title_claims_success(entry, ocr_text)):
        return False, "sin_cierre_verificable", objectives, score, paths, ocr_lines
    if score < 6 or len(ocr_lines) < 5:
        return False, "score_u_ocr_bajo", objectives, score, paths, ocr_lines
    return True, "promovible_qa", objectives, score, paths, ocr_lines


def write_reports(rows, label):
    DOCS_DIR.mkdir(exist_ok=True)
    csv_path = DOCS_DIR / f"reddit_audit_remine_{label}.csv"
    html_path = DOCS_DIR / f"reddit_audit_remine_{label}.html"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "post_id",
                "decision",
                "reason",
                "score",
                "objectives",
                "subreddit",
                "title",
                "source_url",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "post_id": row["post_id"],
                "decision": row["decision"],
                "reason": row["reason"],
                "score": row["score"],
                "objectives": ",".join(row["objectives"]),
                "subreddit": row["subreddit"],
                "title": row["title"],
                "source_url": row["source_url"],
            })

    cards = []
    for row in rows[:300]:
        cls = "ok" if row["decision"] == "promote" else "skip"
        cards.append(
            f"""
            <article class="card {cls}">
              <h2>{html.escape(row['title'] or row['post_id'])}</h2>
              <div class="meta">post {html.escape(row['post_id'])} · {html.escape(row['subreddit'])} · score {row['score']} · {html.escape(row['reason'])}</div>
              <p><strong>Objetivos:</strong> {html.escape(', '.join(row['objectives']) or 'sin objetivo')}</p>
              <pre>{html.escape((row['ocr_text'] or '')[:1800])}</pre>
              <p><a href="{html.escape(row['source_url'] or '#')}">Post original</a></p>
            </article>
            """
        )
    html_path.write_text(
        f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Re-minado auditoria Reddit</title>
<style>
body{{font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;margin:24px}}
.card{{border:1px solid #30363d;border-radius:8px;padding:16px;margin:14px 0;background:#161b22}}
.ok{{border-left:5px solid #22c55e}}.skip{{border-left:5px solid #64748b}}
.meta{{color:#9fb0c3;font-size:13px}}pre{{white-space:pre-wrap;background:#05070a;padding:12px;border-radius:6px;max-height:300px;overflow:auto}}
a{{color:#58a6ff}}
</style></head><body>
<h1>Re-minado local de auditoria Reddit</h1>
<p>Generado: {datetime.now().isoformat(timespec='seconds')}</p>
{''.join(cards)}
</body></html>""",
        encoding="utf-8",
    )
    return csv_path, html_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--min-score", type=int, default=6)
    parser.add_argument("--label", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    existing = {
        row[0]
        for row in cur.execute("SELECT post_id FROM reddit_success_scrape_candidates")
    }
    candidates = cur.execute(
        """
        SELECT *
        FROM reddit_success_scrape_rejected_audit
        WHERE status='rejected_low_score' AND score >= ?
        ORDER BY score DESC, updated_at DESC
        LIMIT ?
        """,
        (args.min_score, args.limit),
    ).fetchall()

    report_rows = []
    promoted = 0
    for row in candidates:
        ok, reason, objectives, score, paths, ocr_lines = evaluate(row)
        decision = "promote" if ok and row["post_id"] not in existing else "skip"
        if ok and row["post_id"] in existing:
            reason = "ya_existe_en_candidate_qa"
        report_rows.append({
            "post_id": row["post_id"],
            "decision": decision,
            "reason": reason,
            "score": score,
            "objectives": objectives,
            "subreddit": row["subreddit"] or "",
            "title": row["title"] or "",
            "source_url": row["source_url"] or "",
            "ocr_text": row["ocr_text"] or "",
        })
        if args.apply and decision == "promote":
            title_es, summary_es = title_and_summary_es(row["title"] or "", objectives, score)
            item = {
                "post_id": row["post_id"],
                "source_url": row["source_url"] or "",
                "title": row["title"] or "",
                "title_es": title_es,
                "subreddit": row["subreddit"] or "",
                "image_urls": parse_json(row["image_urls_json"], []),
                "local_paths": paths,
                "ocr_text": row["ocr_text"] or "",
                "ocr_lines": ocr_lines,
                "translation_es": "",
                "objectives": objectives,
                "score": score,
                "summary_es": summary_es + " Promovido desde auditoria local con QA estricto.",
                "status": "candidate_qa",
                "bytes_downloaded": row["bytes_downloaded"] or 0,
                "discovery_source": f"{row['discovery_source'] or ''}/remine_audit",
                "category": classify_case(objectives, row["title"] or "", row["ocr_text"] or "", len(ocr_lines)),
                "image_hash": row["image_hash"] or "",
                "ocr_hash": row["ocr_hash"] or "",
                "error_message": "promoted_from_rejected_audit",
            }
            save_candidate(conn, item)
            cur.execute(
                "UPDATE reddit_success_scrape_rejected_audit SET status=?, error_message=?, updated_at=? WHERE post_id=?",
                ("promoted_candidate_qa", "promoted_from_rejected_audit", datetime.now().isoformat(timespec="seconds"), row["post_id"]),
            )
            promoted += 1

    if args.apply:
        conn.commit()
    csv_path, html_path = write_reports(report_rows, args.label)
    total_ok = sum(1 for row in report_rows if row["decision"] == "promote")
    print(json.dumps({
        "checked": len(report_rows),
        "promotable": total_ok,
        "promoted": promoted,
        "csv": str(csv_path),
        "html": str(html_path),
    }, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
