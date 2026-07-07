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
RAW_DIR = ROOT / "scratch" / "reddit_objective_dialogue_scan_raw"
ENV_PATHS = [
    ROOT / ".env",
    Path(r"C:\desarrollos\antigravity\scraping  bibiliotera de meta\backend\.env"),
    Path(r"C:\desarrollos\antigravity\Easy Date\.env"),
]

SUBREDDITS = ["Tinder", "Bumble", "OnlineDating", "dating_advice", "seduction"]
QUERIES = [
    'self:yes "got her number"',
    'self:yes "gave me her number"',
    'self:yes "she gave me her number"',
    'self:yes "got the number"',
    'self:yes "asked for her number"',
    'self:yes "responded with her number"',
    'self:yes "phone number"',
    'self:yes "number close"',
    'self:yes "got her snap"',
    'self:yes "snapchat"',
    'self:yes "instagram"',
    'self:yes "whatsapp"',
    'self:yes "got her IG"',
    'self:yes "set up a date"',
    'self:yes "date lined up"',
    'self:yes "agreed to meet"',
    'self:yes "meet up"',
    'self:yes "she said yes" "date"',
]

IMAGE_TERMS = ["<img", "preview.redd.it", "i.redd.it", "imgur.com", "redgifs.com", "gfycat.com"]
BAD_TERMS = ["17 year old", "underage", "under age", "minor", "massage therapist", "escort", "bot", "scam"]
APP_TERMS = ["tinder", "bumble", "hinge", "okcupid", "dating app", "online dating", "matched", "match"]
OBJECTIVE_RULES = [
    ("telefono", ["got her number", "gave me her number", "she gave me her number", "got the number", "phone number", "number close", "asked for her number", "responded with her number"]),
    ("snapchat", ["snapchat", "snap"]),
    ("instagram", ["instagram", " ig ", "her ig", "got her ig"]),
    ("whatsapp", ["whatsapp", "whats app"]),
    ("cita", ["set up a date", "date lined up", "agreed to meet", "meet up", "met up", "she said yes", "went on a date"]),
]
LABEL_MAP = {
    "me": "hombre",
    "i": "hombre",
    "m": "hombre",
    "him": "hombre",
    "guy": "hombre",
    "he": "hombre",
    "her": "mujer",
    "she": "mujer",
    "girl": "mujer",
    "woman": "mujer",
    "f": "mujer",
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EasyDateObjectiveDialogue/1.0",
            "Accept": "application/atom+xml,text/xml,*/*",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        },
        proxies=build_proxy(env),
        timeout=35,
    )
    meter["requests"] += 1
    meter["bytes"] += len(response.content or b"")
    meter["last_status"] = response.status_code
    time.sleep(0.85 + random.random() * 0.6)
    response.raise_for_status()
    return response.text


def strip_html(value):
    value = html.unescape(value or "")
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.S)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</(p|div|li)>", "\n", value, flags=re.I)
    raw = value
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return raw, value.strip()


def post_id_from_url(url):
    match = re.search(r"/comments/([^/]+)/", url)
    return match.group(1) if match else ""


def detect_objectives(title, body):
    haystack = f" {title} {body} ".lower()
    objectives = []
    for name, terms in OBJECTIVE_RULES:
        if any(term in haystack for term in terms):
            objectives.append(name)
    return objectives


def has_app_context(title, body, subreddit):
    haystack = f"{title} {body} {subreddit}".lower()
    return any(term in haystack for term in APP_TERMS)


def extract_turns(body):
    text = re.sub(r"\s+", " ", body)
    pattern = re.compile(r"(?:^|\s)(me|her|she|girl|woman|him|guy|he|i|m|f)\s*(?:-|:)\s*", re.I)
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
            turns.append({"speaker": speaker, "raw_label": label, "text": content[:600]})
    return turns


def alternations(turns):
    return sum(1 for a, b in zip(turns, turns[1:]) if a["speaker"] != b["speaker"])


def parse_feed(xml_text, subreddit, seen_ids):
    root = ET.fromstring(xml_text.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for feed_rank, entry in enumerate(root.findall("a:entry", ns), 1):
        title = entry.findtext("a:title", default="", namespaces=ns)
        raw_html = entry.findtext("a:content", default="", namespaces=ns)
        link_node = entry.find("a:link", ns)
        url = link_node.attrib.get("href", "") if link_node is not None else ""
        post_id = post_id_from_url(url)
        if not post_id or post_id in seen_ids:
            continue
        raw, body = strip_html(raw_html)
        haystack = f"{title} {body}".lower()
        if any(term in f"{raw} {body}".lower() for term in IMAGE_TERMS):
            continue
        if any(term in haystack for term in BAD_TERMS):
            continue
        if not has_app_context(title, body, subreddit):
            continue
        objectives = detect_objectives(title, body)
        if not objectives:
            continue
        turns = extract_turns(body)
        men = sum(1 for turn in turns if turn["speaker"] == "hombre")
        women = sum(1 for turn in turns if turn["speaker"] == "mujer")
        alt = alternations(turns)
        if len(turns) < 4 or men < 2 or women < 2 or alt < 2:
            continue
        score = len(turns) * 10 + alt * 12 + len(objectives) * 35 + max(0, 25 - feed_rank)
        if "cita" in objectives:
            score += 20
        out.append(
            {
                "post_id": post_id,
                "subreddit": subreddit,
                "feed_rank": feed_rank,
                "title": title,
                "url": url,
                "body": body,
                "objectives": objectives,
                "turns": turns[:18],
                "men_turns": men,
                "women_turns": women,
                "alternations": alt,
                "quality_score": score,
            }
        )
    return out


def write_raw(items, meter):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RAW_DIR / f"reddit_objective_dialogues_raw_{stamp}.json"
    json_path.write_text(json.dumps({"meter": meter, "results": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def main():
    env = load_env()
    if not build_proxy(env):
        raise SystemExit("No encontre credenciales PROXY_* en .env.")
    session = requests.Session()
    meter = {"requests": 0, "bytes": 0, "last_status": None}
    seen_ids = existing_post_ids()
    collected = {}

    targets = []
    for subreddit in SUBREDDITS:
        for query in QUERIES:
            targets.append((subreddit, query, True))
    for query in QUERIES:
        targets.append(("global", query, False))

    for subreddit, query, scoped in targets:
        params = {"q": query, "sort": "top", "t": "all"}
        if scoped:
            params["restrict_sr"] = "on"
            url = f"https://old.reddit.com/r/{subreddit}/search.rss?{urlencode(params)}"
            label = f"r/{subreddit}"
        else:
            url = f"https://old.reddit.com/search.rss?{urlencode(params)}"
            label = "global"
        print(f"Buscando {label}: {query}", flush=True)
        try:
            found = parse_feed(fetch(session, url, env, meter), subreddit, seen_ids)
        except Exception as exc:
            print(f"WARN {label} {query}: {exc}", flush=True)
            continue
        for item in found:
            current = collected.get(item["post_id"])
            if current is None or item["quality_score"] > current["quality_score"]:
                collected[item["post_id"]] = item
        if len(collected) >= 16:
            break

    ranked = sorted(collected.values(), key=lambda item: item["quality_score"], reverse=True)
    path = write_raw(ranked[:20], meter)
    print(json.dumps({"count": len(ranked), "selected": min(20, len(ranked)), "meter": meter, "json": str(path)}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
