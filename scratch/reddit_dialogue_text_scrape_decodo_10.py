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
RAW_DIR = ROOT / "scratch" / "reddit_dialogue_text_scan_raw"
ENV_PATHS = [
    ROOT / ".env",
    Path(r"C:\desarrollos\antigravity\scraping  bibiliotera de meta\backend\.env"),
    Path(r"C:\desarrollos\antigravity\Easy Date\.env"),
]

SUBREDDITS = ["Tinder", "Bumble", "OnlineDating", "dating_advice", "seduction"]
QUERY_SETS = [
    ('self:yes "Me -" "Her -" "Tinder"', True),
    ('self:yes "Me -" "She -" "Tinder"', True),
    ('self:yes "Me:" "Her:" "Tinder"', True),
    ('self:yes "Me:" "She:" "Tinder"', True),
    ('self:yes "M:" "F:" "Tinder"', True),
    ('self:yes "Guy:" "Girl:" "Tinder"', True),
    ('self:yes "me:" "her:" "tinder"', True),
    ('self:yes "Her -" "Me -" "Bumble"', True),
    ('self:yes "She -" "Me -" "Bumble"', True),
    ('self:yes "Her:" "Me:" "Bumble"', True),
    ('self:yes "She:" "Me:" "Bumble"', True),
    ('self:yes "M:" "F:" "Bumble"', True),
    ('self:yes "Girl:" "Me:" "Tinder"', True),
    ('self:yes "Woman:" "Me:" "Tinder"', True),
    ('self:yes "Him:" "Her:" "dating app"', True),
    ('self:yes "I said" "she said" "Tinder"', False),
    ('self:yes "I said" "she said" "Bumble"', False),
]

APP_TERMS = [
    "tinder",
    "bumble",
    "hinge",
    "okcupid",
    "dating app",
    "online dating",
    "matched",
    "match",
]
IMAGE_TERMS = ["<img", "preview.redd.it", "i.redd.it", "imgur.com", "redgifs.com", "gfycat.com"]
BAD_TERMS = [
    "17 year old",
    "underage",
    "under age",
    "minor",
    "massage therapist",
    "escort",
    "horror story",
    "waste of time",
]
SUCCESS_TERMS = ["number", "date", "meet", "met up", "kiss", "hookup", "went out", "set up"]

LABEL_MAP = {
    "me": "hombre",
    "i": "hombre",
    "m": "hombre",
    "man": "hombre",
    "him": "hombre",
    "guy": "hombre",
    "he": "hombre",
    "f": "mujer",
    "her": "mujer",
    "she": "mujer",
    "girl": "mujer",
    "woman": "mujer",
}


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
        return {row[0] for row in conn.execute("SELECT post_id FROM reddit_conversations WHERE post_id IS NOT NULL")}
    finally:
        conn.close()


def fetch(session, url, env, meter):
    response = session.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EasyDateDialogueResearch/1.0",
            "Accept": "application/atom+xml,text/xml,*/*",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        },
        proxies=build_proxy(env),
        timeout=35,
    )
    meter["requests"] += 1
    meter["bytes"] += len(response.content or b"")
    meter["last_status"] = response.status_code
    time.sleep(1.0 + random.random() * 0.8)
    response.raise_for_status()
    return response.text


def strip_html(value):
    value = html.unescape(value or "")
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.S)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</(p|div|li)>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def post_id_from_url(url):
    match = re.search(r"/comments/([^/]+)/", url)
    return match.group(1) if match else ""


def has_image(raw_html, body):
    haystack = f"{raw_html} {body}".lower()
    return any(term in haystack for term in IMAGE_TERMS)


def has_app_context(title, body, subreddit):
    haystack = f"{title} {body} {subreddit}".lower()
    return any(term in haystack for term in APP_TERMS)


def extract_labeled_turns(body):
    text = re.sub(r"\s+", " ", body)
    pattern = re.compile(r"(?:^|\s)(me|her|she|girl|woman|him|guy|he|i|m|f|man)\s*(?:-|:)\s*", re.I)
    matches = list(pattern.finditer(text))
    turns = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip(" -:;")
        content = re.sub(r"\s+", " ", content)
        if len(content) < 3:
            continue
        label = match.group(1).lower()
        speaker = LABEL_MAP.get(label)
        if speaker:
            turns.append({"speaker": speaker, "raw_label": label, "text": content[:500]})
    return turns


def alternating_score(turns):
    if len(turns) < 2:
        return 0
    return sum(1 for a, b in zip(turns, turns[1:]) if a["speaker"] != b["speaker"])


def qualifies(title, body, raw_html, require_labels, subreddit):
    lowered = f"{title} {body}".lower()
    if has_image(raw_html, body) or any(term in lowered for term in BAD_TERMS):
        return None
    if not has_app_context(title, body, subreddit):
        return None
    turns = extract_labeled_turns(body)
    men = sum(1 for turn in turns if turn["speaker"] == "hombre")
    women = sum(1 for turn in turns if turn["speaker"] == "mujer")
    alternations = alternating_score(turns)
    if len(turns) < 4 or men < 2 or women < 2 or alternations < 2:
        return None
    success = sum(1 for term in SUCCESS_TERMS if term in lowered)
    score = len(turns) * 12 + alternations * 10 + success * 16
    return {"turns": turns[:16], "men_turns": men, "women_turns": women, "alternations": alternations, "quality_score": score}


def parse_feed(xml_text, subreddit, seen_ids, require_labels):
    root = ET.fromstring(xml_text.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []
    for feed_rank, entry in enumerate(root.findall("a:entry", ns), 1):
        title = entry.findtext("a:title", default="", namespaces=ns)
        raw_html = entry.findtext("a:content", default="", namespaces=ns)
        link_node = entry.find("a:link", ns)
        url = link_node.attrib.get("href", "") if link_node is not None else ""
        post_id = post_id_from_url(url)
        if not post_id or post_id in seen_ids:
            continue
        body = strip_html(raw_html)
        audit = qualifies(title, body, raw_html, require_labels, subreddit)
        if not audit:
            continue
        results.append(
            {
                "post_id": post_id,
                "subreddit": subreddit,
                "feed_rank": feed_rank,
                "title": title,
                "url": url,
                "body": body,
                **audit,
            }
        )
    return results


def write_outputs(results, meter):
    DOCS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RAW_DIR / f"reddit_dialogues_text_top10_{stamp}.json"
    csv_path = DOCS_DIR / f"reddit_dialogues_text_top10_{stamp}.csv"
    html_path = DOCS_DIR / f"reddit_dialogues_text_top10_{stamp}.html"

    json_path.write_text(json.dumps({"meter": meter, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "post_id",
                "subreddit",
                "quality_score",
                "turn_count",
                "men_turns",
                "women_turns",
                "alternations",
                "url",
                "title",
            ],
        )
        writer.writeheader()
        for rank, item in enumerate(results, 1):
            writer.writerow(
                {
                    "rank": rank,
                    "post_id": item["post_id"],
                    "subreddit": item["subreddit"],
                    "quality_score": item["quality_score"],
                    "turn_count": len(item["turns"]),
                    "men_turns": item["men_turns"],
                    "women_turns": item["women_turns"],
                    "alternations": item["alternations"],
                    "url": item["url"],
                    "title": item["title"],
                }
            )

    cards = []
    for rank, item in enumerate(results, 1):
        turns_html = "".join(
            f"<div class='turn {turn['speaker']}'><b>{'Hombre' if turn['speaker'] == 'hombre' else 'Mujer'}</b><p>{html.escape(turn['text'])}</p></div>"
            for turn in item["turns"]
        )
        cards.append(
            f"""
            <article class="case">
              <div class="rank">#{rank}</div>
              <div class="meta">
                <span>r/{html.escape(item['subreddit'])}</span>
                <span>{len(item['turns'])} turnos</span>
                <span>H:{item['men_turns']} / M:{item['women_turns']}</span>
                <span>Alternancia: {item['alternations']}</span>
                <span>Score: {item['quality_score']}</span>
              </div>
              <h2>{html.escape(item['title'])}</h2>
              <a href="{html.escape(item['url'])}" target="_blank" rel="noreferrer">Abrir post original</a>
              <section class="dialogue">{turns_html}</section>
              <details><summary>Texto original completo</summary><p>{html.escape(item['body'][:2400])}</p></details>
            </article>
            """
        )

    mb = meter["bytes"] / (1024 * 1024)
    html_doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Easy Date - Reddit diálogos reales sin imagen</title>
  <style>
    body {{ margin:0; font-family: Arial, sans-serif; background:#101116; color:#f7f8fc; }}
    header {{ padding:28px; background:#191c25; border-bottom:1px solid #303545; }}
    main {{ max-width:1080px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 10px; font-size:28px; }}
    .summary {{ color:#bdc6df; line-height:1.45; }}
    .case {{ position:relative; margin-bottom:22px; padding:22px; background:#191c25; border:1px solid #303545; border-radius:8px; }}
    .rank {{ position:absolute; right:18px; top:18px; color:#ff4b88; font-weight:700; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-right:54px; }}
    .meta span {{ padding:5px 8px; border-radius:999px; background:#252b3a; color:#d0d8ee; font-size:13px; }}
    h2 {{ margin:14px 0 8px; font-size:22px; }}
    a {{ color:#58e0b2; }}
    .dialogue {{ margin-top:18px; display:grid; gap:10px; }}
    .turn {{ max-width:78%; padding:12px 14px; border-radius:16px; }}
    .turn b {{ display:block; margin-bottom:5px; font-size:12px; opacity:.75; }}
    .turn p {{ margin:0; line-height:1.45; }}
    .hombre {{ margin-left:auto; background:#f1dfe3; color:#14151a; border-bottom-right-radius:4px; }}
    .mujer {{ margin-right:auto; background:#050506; color:#f7f8fc; border-bottom-left-radius:4px; }}
    details {{ margin-top:16px; color:#c7cee0; }}
    details p {{ line-height:1.5; }}
    code {{ color:#ffc857; }}
  </style>
</head>
<body>
  <header>
    <h1>10 conversaciones reales textuales sin imagen</h1>
    <div class="summary">
      Filtro: posts RSS de Reddit sin imagen, no existentes en <code>textgame.db</code>, con mínimo 4 turnos extraíbles y ambos hablantes detectados.<br>
      Consumo proxy aproximado: <strong>{mb:.3f} MB</strong> en <strong>{meter['requests']}</strong> requests HTTP.
    </div>
  </header>
  <main>{''.join(cards)}</main>
</body>
</html>
"""
    html_path.write_text(html_doc, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "html": str(html_path)}


def main():
    env = load_env()
    if not build_proxy(env):
        raise SystemExit("No encontre credenciales PROXY_* en .env.")
    session = requests.Session()
    meter = {"requests": 0, "bytes": 0, "last_status": None}
    seen_ids = existing_post_ids()
    collected = {}

    search_targets = []
    for subreddit in SUBREDDITS:
        for query, require_labels in QUERY_SETS:
            search_targets.append((subreddit, query, require_labels, True))
    for query, require_labels in QUERY_SETS:
        search_targets.append(("", query, require_labels, False))

    for subreddit, query, require_labels, restrict_sr in search_targets:
        params = {"q": query, "sort": "top", "t": "all"}
        if restrict_sr:
            params["restrict_sr"] = "on"
            url = f"https://old.reddit.com/r/{subreddit}/search.rss?{urlencode(params)}"
            label = f"r/{subreddit}"
        else:
            url = f"https://old.reddit.com/search.rss?{urlencode(params)}"
            label = "global"
        print(f"Buscando {label}: {query}", flush=True)
        try:
            xml_text = fetch(session, url, env, meter)
            found = parse_feed(xml_text, subreddit or "global", seen_ids, require_labels)
        except Exception as exc:
            print(f"WARN {label} {query}: {exc}", flush=True)
            continue
        for item in found:
            current = collected.get(item["post_id"])
            if current is None or item["quality_score"] > current["quality_score"]:
                collected[item["post_id"]] = item
        if len(collected) >= 10:
            break

    ranked = sorted(collected.values(), key=lambda item: item["quality_score"], reverse=True)[:10]
    paths = write_outputs(ranked, meter)
    print(json.dumps({"count": len(ranked), "meter": meter, "paths": paths}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
