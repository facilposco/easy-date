import argparse
import html
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"

POSITIVE_TITLE_PATTERNS = [
    "got her number",
    "gave me her number",
    "phone number",
    "number ensued",
    "got her whatsapp",
    "got her snap",
    "got her instagram",
    "secured a date",
    "date secured",
    "first date",
    "went on a date",
    "opener worked",
    "worked well",
    "success",
    "hit it off",
]
POSITIVE_OCR_PATTERNS = [
    "text me",
    "call me",
    "my number",
    "my snap",
    "my instagram",
    "my whatsapp",
    "see you",
    "sounds good",
    "let's do it",
    "lets do it",
    "i'm down",
    "im down",
    "would love",
    "definitely",
    "shall shoot ya a message",
]
NEGATIVE_PATTERNS = [
    "bitcoin",
    "hacker",
    "telegram:",
    "prohacker",
    "edit profile",
    "smart photos",
    "prompts",
    "opening move",
    "about me",
    "aboutme",
    "send a compliment",
    "didn't work",
    "didnt work",
    "no response",
    "ghosted",
    "unmatch",
    "piss off",
    "not a good line",
    "didn't feel",
    "didnt feel",
    "no spark",
    "as friends",
    "busy tonight",
    "what should i have said",
]
CHAT_PATTERNS = [
    "you matched",
    "youmatched",
    "type a message",
    "send a message",
    "sent",
    "reply",
    "chat",
    "message",
]


def parse_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def contains_any(text, patterns):
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern in lowered]


def phone_like(text):
    return bool(re.search(r"(?<!\d)(?:\+?\d[\d .()\-]{6,}\d)(?!\d)", text or ""))


def score_review(row):
    title = row["title"] or ""
    ocr = row["ocr_text"] or ""
    hay = f"{title}\n{ocr}"
    objectives = parse_json(row["objectives_json"], [])
    reasons = []
    score = 0

    title_hits = contains_any(title, POSITIVE_TITLE_PATTERNS)
    ocr_hits = contains_any(ocr, POSITIVE_OCR_PATTERNS)
    negative_hits = contains_any(hay, NEGATIVE_PATTERNS)
    chat_hits = contains_any(ocr, CHAT_PATTERNS)

    if title_hits:
        score += min(4, len(title_hits) * 2)
        reasons.append("titulo_exito:" + ",".join(title_hits[:3]))
    if ocr_hits:
        score += min(5, len(ocr_hits) * 2)
        reasons.append("ocr_cierre:" + ",".join(ocr_hits[:3]))
    if phone_like(ocr):
        score += 4
        reasons.append("telefono_patron")
    if chat_hits:
        score += 2
        reasons.append("chat:" + ",".join(chat_hits[:3]))
    if objectives:
        score += min(3, len(objectives))
        reasons.append("objetivos:" + ",".join(objectives))
    if negative_hits:
        score -= min(8, len(negative_hits) * 3)
        reasons.append("negativo:" + ",".join(negative_hits[:3]))
    if row["score"] is not None:
        score += max(0, int(row["score"]) - 5)

    if not chat_hits:
        reasons.append("sin_chat_claro")
        score -= 3
    paths = parse_json(row["local_paths_json"], [])
    existing_paths = [p for p in paths if p and Path(p).exists()]
    if not existing_paths:
        reasons.append("sin_imagen_local")
        score -= 3

    return score, reasons, existing_paths


def ensure_review_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reddit_success_review_queue (
            post_id TEXT PRIMARY KEY,
            source_url TEXT,
            title TEXT,
            subreddit TEXT,
            score INTEGER,
            review_score INTEGER,
            reasons_json TEXT,
            objectives_json TEXT,
            local_paths_json TEXT,
            ocr_excerpt TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()


def upsert_review(conn, row, review_score, reasons, paths):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO reddit_success_review_queue (
            post_id, source_url, title, subreddit, score, review_score,
            reasons_json, objectives_json, local_paths_json, ocr_excerpt,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            source_url=excluded.source_url,
            title=excluded.title,
            subreddit=excluded.subreddit,
            score=excluded.score,
            review_score=excluded.review_score,
            reasons_json=excluded.reasons_json,
            objectives_json=excluded.objectives_json,
            local_paths_json=excluded.local_paths_json,
            ocr_excerpt=excluded.ocr_excerpt,
            status=excluded.status,
            updated_at=excluded.updated_at
        """,
        (
            row["post_id"],
            row["source_url"],
            row["title"],
            row["subreddit"],
            row["score"],
            review_score,
            json.dumps(reasons, ensure_ascii=False),
            row["objectives_json"],
            json.dumps(paths, ensure_ascii=False),
            (row["ocr_text"] or "")[:2500],
            "needs_human_or_llm_qa",
            now,
            now,
        ),
    )


def write_html(rows, label):
    DOCS_DIR.mkdir(exist_ok=True)
    html_path = DOCS_DIR / f"reddit_success_review_queue_{label}.html"
    csv_path = DOCS_DIR / f"reddit_success_review_queue_{label}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("post_id,review_score,score,subreddit,title,source_url,reasons\n")
        for item in rows:
            fh.write(
                ",".join(
                    [
                        item["post_id"],
                        str(item["review_score"]),
                        str(item["score"]),
                        item["subreddit"].replace(",", " "),
                        '"' + item["title"].replace('"', '""') + '"',
                        item["source_url"],
                        '"' + ";".join(item["reasons"]).replace('"', '""') + '"',
                    ]
                )
                + "\n"
            )
    cards = []
    for item in rows[:200]:
        img = ""
        if item["paths"]:
            src = Path(item["paths"][0]).as_uri()
            img = f'<img src="{src}" alt="captura">'
        cards.append(
            f"""
            <article class="case">
              <div class="media">{img}</div>
              <div class="body">
                <h2>{html.escape(item['title'])}</h2>
                <div class="meta">review {item['review_score']} · score {item['score']} · {html.escape(item['subreddit'])} · {html.escape(item['post_id'])}</div>
                <p>{html.escape('; '.join(item['reasons']))}</p>
                <pre>{html.escape(item['ocr'][:2200])}</pre>
                <a href="{html.escape(item['source_url'])}">Post original</a>
              </div>
            </article>
            """
        )
    html_path.write_text(
        f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cola QA Natalia Reddit</title>
<style>
body{{background:#0b0f14;color:#e5edf6;font-family:Arial,sans-serif;margin:24px}}
.case{{display:grid;grid-template-columns:minmax(240px,38%) 1fr;gap:20px;border:1px solid #263241;border-radius:8px;margin:16px 0;padding:16px;background:#131a23}}
img{{max-width:100%;border-radius:6px;background:#fff}}.meta{{color:#9fb1c4;font-size:13px}}pre{{white-space:pre-wrap;background:#06090d;padding:12px;border-radius:6px;max-height:360px;overflow:auto}}a{{color:#58a6ff}}
@media(max-width:900px){{.case{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>Cola de revisión fuerte para Natalia</h1>
<p>Estos casos NO están aprobados para RAG; requieren QA humano o LLM. Generado {datetime.now().isoformat(timespec='seconds')}.</p>
{''.join(cards)}
</body></html>""",
        encoding="utf-8",
    )
    return csv_path, html_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-review-score", type=int, default=7)
    parser.add_argument("--label", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    ensure_review_table(conn)
    rows = conn.execute(
        """
        SELECT *
        FROM reddit_success_scrape_rejected_audit
        WHERE status='rejected_low_score' AND score >= 5
        ORDER BY score DESC, updated_at DESC
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()
    selected = []
    for row in rows:
        review_score, reasons, paths = score_review(row)
        if review_score >= args.min_review_score:
            upsert_review(conn, row, review_score, reasons, paths)
            selected.append(
                {
                    "post_id": row["post_id"],
                    "source_url": row["source_url"] or "",
                    "title": row["title"] or "",
                    "subreddit": row["subreddit"] or "",
                    "score": row["score"] or 0,
                    "review_score": review_score,
                    "reasons": reasons,
                    "paths": paths,
                    "ocr": row["ocr_text"] or "",
                }
            )
    conn.commit()
    selected.sort(key=lambda item: item["review_score"], reverse=True)
    csv_path, html_path = write_html(selected, args.label)
    print(json.dumps({"checked": len(rows), "queued": len(selected), "csv": str(csv_path), "html": str(html_path)}, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
