import csv
import html
import json
import random
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode

import requests


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"
RAW_DIR = ROOT / "scratch" / "reddit_text_scan_raw"
ENV_PATHS = [
    ROOT / ".env",
    Path(r"C:\desarrollos\antigravity\scraping  bibiliotera de meta\backend\.env"),
    Path(r"C:\desarrollos\antigravity\Easy Date\.env"),
]

SUBREDDITS = ["Tinder", "Bumble", "OnlineDating"]
QUERIES = [
    'self:yes "Tinder Success"',
    'self:yes "success story"',
    'self:yes "successful tinder"',
    'self:yes "successful bumble"',
    'self:yes "got her number"',
    'self:yes "got the number"',
    'self:yes "got a date"',
    'self:yes "set up a date"',
    'self:yes "text game"',
    'self:yes "tinder conversation"',
    'self:yes "bumble conversation"',
    'self:yes "she said" "I said"',
]

SIGNALS = [
    r"\bme\s*:",
    r"\bher\s*:",
    r"\bshe\s+said\b",
    r"\bi\s+said\b",
    r"\btexted\b",
    r"\bconversation\b",
    r"\bnumber\b",
    r"\bdate\b",
    r"\btinder\b",
    r"\bbumble\b",
]

EXCLUDE = [
    "17 year old",
    "underage",
    "minor",
    "high school",
    "massage therapist",
    "imgur.com",
    "i.redd.it",
    "preview.redd.it",
    "blocked before meeting",
    "tanked",
    "cancelled",
    "uncomfortable",
    "will i get in trouble",
    "need advice",
    "not that attractive",
]

SUCCESS_TERMS = [
    "success",
    "successful",
    "got her number",
    "got the number",
    "got a date",
    "set up a date",
    "meet up",
    "met up",
    "date lined up",
]

NEGATIVE_TERMS = [
    "blocked",
    "ghosted",
    "cancelled",
    "tanked",
    "scam",
    "played",
    "mia",
    "trouble",
]


def load_env():
    env = {}
    for path in ENV_PATHS:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def build_proxy(env):
    required = ["PROXY_HOST", "PROXY_PORT", "PROXY_USERNAME", "PROXY_PASSWORD"]
    if not all(env.get(key) for key in required):
        return None
    session_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    username = env["PROXY_USERNAME"]
    if "_session-" not in username and "-session-" not in username:
        username = f"{username}_session-{session_id}"
    proxy = f"http://{quote(username)}:{quote(env['PROXY_PASSWORD'])}@{env['PROXY_HOST']}:{env['PROXY_PORT']}"
    return {"http": proxy, "https": proxy}


def existing_post_ids():
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT post_id FROM reddit_conversations WHERE post_id IS NOT NULL").fetchall()
        return {row[0] for row in rows if row and row[0]}
    finally:
        conn.close()


def fetch_text(session, url, proxy_source, meter, sleep_seconds=1.1):
    proxies = build_proxy(proxy_source) if "PROXY_HOST" in proxy_source else proxy_source
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EasyDateResearch/1.0",
        "Accept": "application/atom+xml,text/xml,*/*",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    }
    response = session.get(url, headers=headers, proxies=proxies, timeout=35)
    meter["requests"] += 1
    meter["bytes"] += len(response.content or b"")
    meter["last_status"] = response.status_code
    time.sleep(sleep_seconds + random.random() * 0.7)
    response.raise_for_status()
    return response.text


def strip_tags(value):
    value = html.unescape(value or "")
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.S)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</p>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def post_id_from_url(url):
    match = re.search(r"/comments/([^/]+)/", url)
    return match.group(1) if match else ""


def score_text(title, body, feed_rank):
    haystack = f"{title}\n{body}".lower()
    signal_count = sum(1 for pattern in SIGNALS if re.search(pattern, haystack))
    success_count = sum(1 for term in SUCCESS_TERMS if term in haystack)
    negative_count = sum(1 for term in NEGATIVE_TERMS if term in haystack)
    quote_bonus = 1 if any(mark in body for mark in ['"', "“", "”", "'"]) else 0
    length_bonus = min(len(body) // 350, 5)
    rank_bonus = max(0, 30 - feed_rank)
    return signal_count * 18 + success_count * 24 + quote_bonus * 8 + length_bonus * 5 + rank_bonus - negative_count * 20


def has_image(content):
    lowered = (content or "").lower()
    return (
        "<img" in lowered
        or "preview.redd.it" in lowered
        or "i.redd.it" in lowered
        or "imgur.com" in lowered
        or "redgifs.com" in lowered
        or "gfycat.com" in lowered
    )


def parse_feed(xml_text, subreddit, seen_ids):
    root = ET.fromstring(xml_text.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = []
    for rank, entry in enumerate(root.findall("a:entry", ns), 1):
        title = entry.findtext("a:title", default="", namespaces=ns)
        content_html = entry.findtext("a:content", default="", namespaces=ns)
        link_node = entry.find("a:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        post_id = post_id_from_url(link)
        body = strip_tags(content_html)
        haystack = f"{title} {body}".lower()
        if not post_id or post_id in seen_ids:
            continue
        if has_image(content_html):
            continue
        if len(body) < 220:
            continue
        if any(term in haystack for term in EXCLUDE):
            continue
        if not any(term in haystack for term in SUCCESS_TERMS):
            continue
        if sum(1 for pattern in SIGNALS if re.search(pattern, haystack)) < 2:
            continue
        entries.append(
            {
                "post_id": post_id,
                "subreddit": subreddit,
                "title": title,
                "url": link,
                "body": body,
                "feed_rank": rank,
                "quality_score": score_text(title, body, rank),
            }
        )
    return entries


def parse_comments(xml_text):
    root = ET.fromstring(xml_text.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    comments = []
    for entry in root.findall("a:entry", ns):
        title = entry.findtext("a:title", default="", namespaces=ns)
        content = strip_tags(entry.findtext("a:content", default="", namespaces=ns))
        author_node = entry.find("a:author/a:name", ns)
        author = author_node.text if author_node is not None else ""
        if content and content not in {"[deleted]", "[removed]"} and "submitted by" not in content.lower():
            comments.append({"author": author, "title": title, "body": content})
    return comments[:6]


def excerpt(text, limit):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def write_outputs(results, meter):
    DOCS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RAW_DIR / f"reddit_text_posts_top10_{stamp}.json"
    csv_path = DOCS_DIR / f"reddit_text_posts_top10_{stamp}.csv"
    html_path = DOCS_DIR / f"reddit_text_posts_top10_{stamp}.html"

    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"), "meter": meter, "results": results}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["rank", "post_id", "subreddit", "quality_score", "feed_rank", "url", "title"],
        )
        writer.writeheader()
        for rank, item in enumerate(results, 1):
            writer.writerow({**{key: item[key] for key in writer.fieldnames if key != "rank"}, "rank": rank})

    cases = []
    for rank, item in enumerate(results, 1):
        comments = "".join(
            f"<li><strong>{html.escape(c.get('author') or 'usuario')}:</strong> {html.escape(excerpt(c.get('body'), 420))}</li>"
            for c in item.get("comments", [])
        )
        if not comments:
            comments = "<li>No se consultaron comentarios para ahorrar proxy y evitar 429; el caso usa el texto original del post.</li>"
        cases.append(
            f"""
            <article class="case">
              <div class="rank">#{rank}</div>
              <div class="meta">
                <span>r/{html.escape(item['subreddit'])}</span>
                <span>Calidad: {item['quality_score']}/150 aprox.</span>
                <span>Ranking feed: {item['feed_rank']}</span>
                <span>Sin imagen detectada</span>
              </div>
              <h2>{html.escape(item['title'])}</h2>
              <a href="{html.escape(item['url'])}" target="_blank" rel="noreferrer">Abrir post original</a>
              <section>
                <h3>Conversación/texto original</h3>
                <p>{html.escape(excerpt(item['body'], 1800))}</p>
              </section>
              <section>
                <h3>Comentarios capturados</h3>
                <ul>{comments}</ul>
              </section>
            </article>
            """
        )

    mb = meter["bytes"] / (1024 * 1024)
    html_doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Easy Date - Reddit texto sin imagen</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #101116; color: #f7f8fc; }}
    header {{ padding: 28px; background: #191c25; border-bottom: 1px solid #303545; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 10px; font-size: 28px; }}
    .summary {{ color: #bdc6df; line-height: 1.45; }}
    .case {{ position: relative; margin-bottom: 22px; padding: 22px; background: #191c25; border: 1px solid #303545; border-radius: 8px; }}
    .rank {{ position: absolute; right: 18px; top: 18px; color: #ff4b88; font-weight: 700; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-right: 54px; }}
    .meta span {{ padding: 5px 8px; border-radius: 999px; background: #252b3a; color: #d0d8ee; font-size: 13px; }}
    h2 {{ margin: 14px 0 8px; font-size: 22px; }}
    h3 {{ margin: 18px 0 8px; color: #89b4ff; font-size: 16px; }}
    a {{ color: #58e0b2; }}
    p, li {{ color: #e7ebf6; line-height: 1.55; }}
    ul {{ padding-left: 20px; }}
    code {{ color: #ffc857; }}
  </style>
</head>
<body>
  <header>
    <h1>10 posts de Reddit sin imagen</h1>
    <div class="summary">
      Filtro: RSS de Reddit, operador <code>self:yes</code>, sin etiquetas de imagen ni dominios <code>redd.it</code>, y no existentes en <code>textgame.db</code>.<br>
      Consumo proxy aproximado: <strong>{mb:.3f} MB</strong> en <strong>{meter['requests']}</strong> requests HTTP. La cifra mide cuerpo descargado, no facturación exacta del proveedor. Reddit RSS no expone upvotes exactos; se usó <code>sort=top</code> más scoring local.
    </div>
  </header>
  <main>{''.join(cases)}</main>
</body>
</html>
"""
    html_path.write_text(html_doc, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "html": str(html_path)}


def main():
    env = load_env()
    if not build_proxy(env):
        raise SystemExit("No encontre credenciales PROXY_* en .env.")

    meter = {"requests": 0, "bytes": 0, "last_status": None}
    session = requests.Session()
    seen_ids = existing_post_ids()
    collected = {}

    for subreddit in SUBREDDITS:
        for query in QUERIES:
            params = urlencode({"q": query, "restrict_sr": "on", "sort": "top", "t": "all"})
            url = f"https://old.reddit.com/r/{subreddit}/search.rss?{params}"
            print(f"Buscando r/{subreddit}: {query}", flush=True)
            try:
                xml_text = fetch_text(session, url, env, meter)
            except Exception as exc:
                print(f"WARN {subreddit} {query}: {exc}", flush=True)
                continue
            for item in parse_feed(xml_text, subreddit, seen_ids):
                current = collected.get(item["post_id"])
                if current is None or item["quality_score"] > current["quality_score"]:
                    collected[item["post_id"]] = item
            if len(collected) >= 60:
                break
        if len(collected) >= 60:
            break

    ranked = sorted(collected.values(), key=lambda item: item["quality_score"], reverse=True)[:10]
    for item in ranked:
        item["comments"] = []

    paths = write_outputs(ranked, meter)
    print(json.dumps({"count": len(ranked), "meter": meter, "paths": paths}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
