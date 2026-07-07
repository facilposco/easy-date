import argparse
import csv
import hashlib
import html
import json
import os
import random
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"
IMG_DIR = ROOT / "imagenes_nuevas"
RAW_DIR = ROOT / "scratch" / "reddit_success_image_pipeline"
RSS_CACHE_DIR = ROOT / "scratch" / "cache" / "reddit_rss"
GUIDE_EXTRACT = DOCS_DIR / "easy_tips_v23_extracto_scoring.txt"

SUBREDDITS = [
    "Tinder",
    "Bumble",
    "hingeapp",
    "OkCupid",
    "Tinderpickuplines",
    "OnlineDating",
    "DatingApps",
    "HingeApp",
    "TinderSuccess",
    "texts",
    "dating",
    "dating_advice",
    "OnlineDatingAdvice",
    "seduction",
    "socialskills",
]
QUERIES = [
    '"got her number"',
    '"she gave me her number"',
    '"exchanged numbers"',
    '"got the number"',
    '"asked for her number"',
    '"gave me her number"',
    '"her number"',
    '"number close"',
    '"phone number"',
    '"text me"',
    '"got his number"',
    '"got her snap"',
    '"gave me her snap"',
    '"got her snapchat"',
    '"snapchat"',
    '"got her insta"',
    '"gave me her instagram"',
    '"instagram"',
    '"whatsapp"',
    '"date tonight"',
    '"got a date"',
    '"secured a date"',
    '"she said yes"',
    '"agreed to meet"',
    '"going on a date"',
    '"went on a date"',
    '"set up a date"',
    '"first date"',
    '"coffee date"',
    '"drinks date"',
    '"asked her out"',
    '"meeting up"',
    '"met up"',
    '"we are meeting"',
    '"smooth"',
    '"actually worked"',
    '"this worked"',
    '"worked on tinder"',
    '"worked on bumble"',
    '"worked on hinge"',
    '"made her laugh"',
    '"great conversation"',
    '"best conversation"',
    '"conversation went well"',
    '"vibed"',
    '"clicked"',
    '"we got engaged"',
    '"tinder win"',
    '"bumble win"',
    '"hinge win"',
    '"success story"',
    '"first Tinder conversation"',
    '"pickup line"',
    '"opener"',
    '"rizz"',
    '"success"',
    '"drinks"',
    '"coffee"',
]

MULTILINGUAL_QUERIES = [
    # German
    '"nummer bekommen"',
    '"ihre nummer"',
    '"handynummer"',
    '"date bekommen"',
    '"treffen ausgemacht"',
    '"tinder erfolg"',
    # Spanish
    '"me dio su numero"',
    '"me paso su numero"',
    '"me dio su whatsapp"',
    '"consegui cita"',
    '"quedamos para salir"',
    '"funciono en tinder"',
    # Portuguese
    '"me deu o numero"',
    '"me passou o whatsapp"',
    '"consegui o whatsapp"',
    '"marquei um encontro"',
    '"deu certo no tinder"',
    # French
    '"elle m a donne son numero"',
    '"j ai eu son numero"',
    '"son snap"',
    '"rendez vous tinder"',
    '"on va se voir"',
    # Italian
    '"mi ha dato il numero"',
    '"ho preso il numero"',
    '"mi ha dato whatsapp"',
    '"appuntamento tinder"',
    '"ci vediamo"',
]

BROAD_SUCCESS_QUERIES = [
    "tinder got her number",
    "bumble got her number",
    "hinge got her number",
    "tinder phone number",
    "bumble phone number",
    "hinge phone number",
    "tinder got her instagram",
    "bumble got her instagram",
    "hinge got her instagram",
    "tinder got her snapchat",
    "bumble got her snapchat",
    "hinge got her snapchat",
    "tinder got a date",
    "bumble got a date",
    "hinge got a date",
    "tinder date secured",
    "bumble date secured",
    "hinge date secured",
    "tinder asked her out",
    "bumble asked her out",
    "hinge asked her out",
    "tinder she said yes",
    "bumble she said yes",
    "hinge she said yes",
    "tinder meeting up",
    "bumble meeting up",
    "hinge meeting up",
    "tinder drinks this weekend",
    "bumble drinks this weekend",
    "hinge drinks this weekend",
    "tinder coffee date",
    "bumble coffee date",
    "hinge coffee date",
    "tinder opener worked",
    "bumble opener worked",
    "hinge opener worked",
    "tinder made her laugh",
    "bumble made her laugh",
    "hinge made her laugh",
    "dating app got her number",
    "dating app got a date",
    "dating app opener worked",
    "dating app conversation went well",
    "online dating got her number",
    "online dating got a date",
    "online dating asked her out",
    "texting got her number",
    "texting asked her out",
    "texting date secured",
    # Spanish
    "tinder me dio su whatsapp",
    "bumble me dio su whatsapp",
    "hinge me dio su whatsapp",
    "tinder me dio su numero",
    "bumble me dio su numero",
    "hinge me dio su numero",
    "tinder consegui cita",
    "bumble consegui cita",
    "hinge consegui cita",
    "tinder quedamos para salir",
    "bumble quedamos para salir",
    "hinge quedamos para salir",
    # Portuguese
    "tinder me passou o whatsapp",
    "bumble me passou o whatsapp",
    "hinge me passou o whatsapp",
    "tinder marquei um encontro",
    "bumble marquei um encontro",
    "hinge marquei um encontro",
    # French
    "tinder elle m a donne son numero",
    "bumble elle m a donne son numero",
    "hinge elle m a donne son numero",
    "tinder rendez vous",
    "bumble rendez vous",
    "hinge rendez vous",
    # German
    "tinder nummer bekommen",
    "bumble nummer bekommen",
    "hinge nummer bekommen",
    "tinder date bekommen",
    "bumble date bekommen",
    "hinge date bekommen",
    # Italian
    "tinder mi ha dato il numero",
    "bumble mi ha dato il numero",
    "hinge mi ha dato il numero",
    "tinder appuntamento",
    "bumble appuntamento",
    "hinge appuntamento",
]

QUERIES = list(dict.fromkeys(BROAD_SUCCESS_QUERIES + QUERIES + MULTILINGUAL_QUERIES))


def media_first_query(query):
    if "self:" in query.lower():
        return query
    return f"{query} self:no"

OBJECTIVE_TERMS = {
    "telefono": [
        "number", "phone", "text me", "digits", "contact",
        "nummer", "handynummer",
        "numero", "telefono",
        "numero", "telefone",
        "numero", "telephone",
        "numero", "cellulare",
    ],
    "whatsapp": ["whatsapp", "whats app"],
    "instagram": ["instagram", "insta", " ig "],
    "snapchat": ["snapchat", "snap"],
    "cita": [
        "date", "drinks", "drink", "coffee", "brunch", "mimosas", "dinner", "meet", "hang out", "hangout", "tonight", "weekend",
        "treffen", "verabredung", "kaffee",
        "cita", "salir", "quedar", "quedamos", "cafe",
        "encontro", "sair", "marquei",
        "rendez vous", "rendez-vous", "boire un verre",
        "appuntamento", "vediamo", "uscire",
    ],
}

QUALITY_TERMS = [
    "smooth",
    "funny",
    "lol",
    "haha",
    "lmao",
    "date",
    "number",
    "text me",
    "drink",
    "coffee",
    "brunch",
    "mimosas",
    "dinner",
    "meet",
    "yes",
    "sure",
    "sounds great",
    "love",
    "funciono",
    "deu certo",
    "erfolg",
    "bien joue",
    "successo",
]

NEGATIVE_TERMS = [
    "crazy",
    "not compatible",
    "incompatible",
    "ghosted",
    "flake",
    "flaked",
    "stopped replying",
    "stopped responding",
    "stops responding",
    "no response",
    "left on read",
    "unmatched",
    "blocked",
    "scam",
    "bot",
    "fake number",
    "stood up",
    "onlyfans",
    "escort",
    "sugar",
    "venmo",
    "cashapp",
    "crypto",
    "harassment",
    "creepy",
    "red flag",
    "got mad",
    "nice guy",
    "good ass guy",
    "threatened me",
]


def slugify(value):
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "sin-categoria"


def read_env():
    env = {}
    path = ROOT / ".env"
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        auth_match = re.search(r'["\']?authorization["\']?\s*:\s*["\'](Basic\s+[^"\']+)["\']', stripped, re.I)
        if auth_match:
            env.setdefault("DECODO_API_AUTH", auth_match.group(1).strip())
            continue
        token_match = re.search(r"basic\s+token\s+\w+\s*:\s*(\S+)", stripped, re.I)
        if token_match:
            env.setdefault("DECODO_API_AUTH", token_match.group(1).strip())
            continue
        url_match = re.search(r'["\']?url["\']?\s*[:=]\s*["\']([^"\']*scraper-api\.decodo\.com[^"\']*)["\']', stripped, re.I)
        if url_match:
            env.setdefault("DECODO_API_URL", url_match.group(1).strip())
            continue
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    for key in ["DECODO_API_MODE", "DECODO_API_PROXY_POOL", "DECODO_API_TARGET", "DECODO_API_HEADLESS"]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def proxy_from(env, prefix):
    host = env.get(f"{prefix}_PROXY_HOST")
    port = env.get(f"{prefix}_PROXY_PORT")
    user = env.get(f"{prefix}_PROXY_USERNAME")
    password = env.get(f"{prefix}_PROXY_PASSWORD")
    if prefix == "":
        host = env.get("PROXY_HOST")
        port = env.get("PROXY_PORT")
        user = env.get("PROXY_USERNAME")
        password = env.get("PROXY_PASSWORD")
    if not all([host, port, user, password]):
        return None
    session_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    if "_session-" not in user and "-session-" not in user:
        user = f"{user}_session-{session_id}"
    proxy = f"http://{quote(user)}:{quote(password)}@{host}:{port}"
    return {"http": proxy, "https": proxy}


def decodo_api_credentials(env):
    user = env.get("DECODO_API_USERNAME") or env.get("DECODO_USERNAME")
    password = env.get("DECODO_API_PASSWORD") or env.get("DECODO_PASSWORD")
    token = env.get("DECODO_API_AUTH") or env.get("DECODO_AUTHORIZATION")
    if token:
        return {"headers": {"Authorization": token if token.lower().startswith("basic ") else f"Basic {token}"}}
    if user and password:
        return {"auth": (user, password)}
    return None


def fetch_decodo_api(env, target_url):
    creds = decodo_api_credentials(env)
    if not creds:
        return None
    api_url = env.get("DECODO_API_URL", "https://scraper-api.decodo.com/v2/scrape")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    headers.update(creds.get("headers", {}))
    payload = {
        "target": env.get("DECODO_API_TARGET", "universal"),
        "url": target_url,
        "proxy_pool": env.get("DECODO_API_PROXY_POOL", "standard"),
    }
    headless = env.get("DECODO_API_HEADLESS")
    if headless:
        payload["headless"] = headless
    last_exc = None
    for attempt in range(4):
        try:
            res = requests.post(api_url, json=payload, headers=headers, auth=creds.get("auth"), timeout=90)
            if res.status_code == 429:
                time.sleep(2 + attempt * 4)
                continue
            res.raise_for_status()
            break
        except Exception as exc:
            last_exc = exc
            if attempt == 3:
                raise
            time.sleep(1 + attempt * 2)
    else:
        raise RuntimeError(last_exc or "decodo request failed")
    data = res.json()
    results = data.get("results") or []
    if not results:
        raise RuntimeError("decodo returned no results")
    content = results[0].get("content") or ""
    if not content:
        raise RuntimeError("decodo returned empty content")
    return content, len(content.encode("utf-8"))


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reddit_success_scrape_candidates (
            post_id TEXT PRIMARY KEY,
            source_url TEXT,
            title TEXT,
            title_es TEXT,
            subreddit TEXT,
            image_urls_json TEXT,
            local_paths_json TEXT,
            ocr_text TEXT,
            ocr_lines_json TEXT,
            translation_es TEXT,
            objectives_json TEXT,
            score INTEGER,
            summary_es TEXT,
            status TEXT,
            bytes_downloaded INTEGER DEFAULT 0,
            discovery_source TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(reddit_success_scrape_candidates)")}
    migrations = {
        "category": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN category TEXT",
        "image_hash": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN image_hash TEXT",
        "ocr_hash": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN ocr_hash TEXT",
        "error_message": "ALTER TABLE reddit_success_scrape_candidates ADD COLUMN error_message TEXT",
    }
    for column, sql in migrations.items():
        if column not in columns:
            conn.execute(sql)
    conn.commit()
    return conn


def existing_ids(conn):
    ids = {row[0] for row in conn.execute("SELECT post_id FROM reddit_conversations WHERE post_id IS NOT NULL")}
    ids.update(
        row[0]
        for row in conn.execute(
            """
            SELECT post_id
            FROM reddit_success_scrape_candidates
            WHERE post_id IS NOT NULL
              AND status IN ('candidate_qa', 'approved_for_natalia', 'duplicate_content')
            """
        )
    )
    return ids


def existing_hashes(conn):
    hashes = {"image": set(), "ocr": set()}
    for image_hash, ocr_hash in conn.execute(
        """
        SELECT image_hash, ocr_hash
        FROM reddit_success_scrape_candidates
        WHERE status IN ('candidate_qa', 'approved_for_natalia')
        """
    ):
        if image_hash:
            hashes["image"].add(image_hash)
        if ocr_hash:
            hashes["ocr"].add(ocr_hash)
    return hashes


def cache_key(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def fetch_rss(session, env, subreddit, query, sort="top", time_window="all"):
    if subreddit in {"global", "all"} or str(subreddit).startswith("__global"):
        params = urlencode({"q": query, "sort": sort, "t": time_window})
        url = f"https://old.reddit.com/search.rss?{params}"
    else:
        params = urlencode({"q": query, "restrict_sr": "on", "sort": sort, "t": time_window})
        url = f"https://old.reddit.com/r/{subreddit}/search.rss?{params}"
    cache_path = RSS_CACHE_DIR / f"{cache_key(url)}.xml"
    if cache_path.exists():
        text = cache_path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            return text, 0
    headers = {"User-Agent": "Mozilla/5.0 EasyDateSuccessScan/1.0", "Accept": "application/atom+xml,text/xml,*/*"}
    last_error = None
    decodo_mode = (env.get("DECODO_API_MODE") or "").lower()
    if decodo_mode in {"preferred", "prefer", "primary", "force", "1", "true", "yes"}:
        try:
            decodo_result = fetch_decodo_api(env, url)
            if decodo_result:
                RSS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(decodo_result[0], encoding="utf-8")
                return decodo_result
        except Exception as decodo_exc:
            last_error = f"decodo_api: {decodo_exc}"
            if decodo_mode == "force":
                raise RuntimeError(last_error)
    for source, proxies in [("direct", None), ("metadata_proxy", proxy_from(env, ""))]:
        try:
            res = session.get(url, headers=headers, proxies=proxies, timeout=35)
            res.raise_for_status()
            RSS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(res.text, encoding="utf-8")
            return res.text, len(res.content)
        except Exception as exc:
            last_error = f"{source}: {exc}"
            if source == "direct":
                try:
                    decodo_result = fetch_decodo_api(env, url)
                    if decodo_result:
                        RSS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                        cache_path.write_text(decodo_result[0], encoding="utf-8")
                        return decodo_result
                except Exception as decodo_exc:
                    last_error = f"decodo_api: {decodo_exc}"
    raise RuntimeError(last_error or "rss fetch failed")


def fetch_post_score(session, env, post_id, allow_decodo=True, allow_dataimpulse=False):
    if not post_id:
        return None
    url = f"https://www.reddit.com/comments/{post_id}.json?raw_json=1"
    headers = {"User-Agent": "Mozilla/5.0 EasyDateSuccessScan/1.0", "Accept": "application/json,*/*"}
    last_error = None
    for source, proxies in [("direct", None), ("metadata_proxy", proxy_from(env, ""))]:
        try:
            res = session.get(url, headers=headers, proxies=proxies, timeout=25)
            res.raise_for_status()
            data = res.json()
            return data[0]["data"]["children"][0]["data"].get("score")
        except Exception as exc:
            last_error = f"{source}: {exc}"
    if allow_dataimpulse:
        try:
            res = session.get(url, headers=headers, proxies=proxy_from(env, "DATAIMPULSE"), timeout=25)
            res.raise_for_status()
            data = res.json()
            return data[0]["data"]["children"][0]["data"].get("score")
        except Exception as exc:
            last_error = f"dataimpulse: {exc}"
    if allow_decodo:
        try:
            content, _ = fetch_decodo_api(env, url)
            data = json.loads(content)
            return data[0]["data"]["children"][0]["data"].get("score")
        except Exception as exc:
            last_error = f"decodo_api: {exc}"
    raise RuntimeError(last_error or "score fetch failed")


def parse_entries(xml_text):
    root = ET.fromstring(xml_text.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns):
        title = entry.findtext("a:title", default="", namespaces=ns)
        content = entry.findtext("a:content", default="", namespaces=ns)
        link_node = entry.find("a:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        post_id = ""
        match = re.search(r"/comments/([^/]+)/", link)
        if match:
            post_id = match.group(1)
        soup = BeautifulSoup(content or "", "html.parser")
        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and not any(skip in src.lower() for skip in ["emoji", "award", "avatar"]):
                imgs.append(html.unescape(src))
        yield {"post_id": post_id, "title": title, "url": link, "image_urls": list(dict.fromkeys(imgs))}


def candidate_image_urls(url):
    urls = [url]
    parsed = urlparse(url)
    if "preview.redd.it" in parsed.netloc:
        clean = url.split("?")[0].replace("preview.redd.it", "i.redd.it")
        urls.insert(0, clean)
    return list(dict.fromkeys(urls))


def download_image(session, env, post_id, image_url, index):
    post_dir = IMG_DIR / f"post_{post_id}"
    post_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"
    out = post_dir / f"img_{index:03d}{suffix}"
    if out.exists() and out.stat().st_size > 1000:
        return out, 0, "existing"
    headers = {"User-Agent": "Mozilla/5.0 EasyDateImageDownload/1.0"}
    last_error = None
    for source, proxies in [("direct", None), ("dataimpulse", proxy_from(env, "DATAIMPULSE"))]:
        for u in candidate_image_urls(image_url):
            try:
                res = session.get(u, headers=headers, proxies=proxies, timeout=45)
                if res.status_code >= 400 or not res.content or len(res.content) < 1000:
                    last_error = f"{source}:{res.status_code}"
                    continue
                ctype = res.headers.get("content-type", "")
                if "image" not in ctype and not u.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    last_error = f"{source}:not-image:{ctype}"
                    continue
                out.write_bytes(res.content)
                return out, len(res.content), source
            except Exception as exc:
                last_error = f"{source}:{exc}"
    raise RuntimeError(last_error or "download failed")


def run_ocr(engine, image_paths):
    lines = []
    for path in image_paths:
        result, _ = engine(str(path))
        if not result:
            continue
        for row in result:
            text = str(row[1]).strip()
            conf = float(row[2]) if len(row) > 2 else 0.0
            if text and conf >= 0.45:
                lines.append({"image": str(path), "text": text, "confidence": conf})
    ocr_text = "\n".join(line["text"] for line in lines)
    return ocr_text, lines


def sha256_file_prefix(path, length=16):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:length]


def combined_image_hash(local_paths):
    digest = hashlib.sha256()
    for path in local_paths:
        digest.update(sha256_file_prefix(path).encode("ascii"))
    return digest.hexdigest()[:16]


def normalized_text_hash(text):
    cleaned = re.sub(r"\s+", " ", (text or "").lower()).strip()
    if not cleaned:
        return ""
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]


def detect_objectives(title, ocr_text):
    hay = f" {title} {ocr_text} ".lower()
    found = []
    for name, terms in OBJECTIVE_TERMS.items():
        if any(term in hay for term in terms):
            found.append(name)
    return found


def score_case(title, ocr_text, objectives, line_count):
    hay = f" {title} {ocr_text} ".lower()
    score = 1
    score += min(3, len(objectives) * 2)
    score += 2 if line_count >= 8 else 1 if line_count >= 5 else 0
    score += min(3, sum(1 for term in QUALITY_TERMS if term in hay))
    if any(term in hay for term in NEGATIVE_TERMS):
        score -= 4
    return max(1, min(10, score))


def has_negative_outcome(title, ocr_text):
    hay = f" {title} {ocr_text} ".lower()
    return any(term in hay for term in NEGATIVE_TERMS)


def classify_case(objectives, title, ocr_text, line_count):
    objective_set = set(objectives)
    hay = f" {title} {ocr_text} ".lower()
    if "cita" in objective_set:
        return "cita_lograda"
    if objective_set & {"telefono", "whatsapp", "instagram", "snapchat"}:
        return "contacto_logrado"
    if any(term in hay for term in ["opener", "pickup line", "smooth", "funny", "rizz"]) or line_count < 8:
        return "abridor_ingenioso"
    if line_count >= 10:
        return "conexion_larga"
    return "potencial_para_revision"


def gemini_keys(env):
    return [value for key, value in sorted(env.items()) if key.startswith("GEMINI_API_KEY_") and value]


def translate_text_gemini(env, text):
    keys = gemini_keys(env)
    if not keys or not text.strip():
        return ""
    prompt = (
        "Traduce y corrige al espanol latino natural la siguiente conversacion OCR. "
        "No inventes mensajes. Conserva el orden, saltos de linea y sentido. "
        "Si el OCR junta palabras, separalas solo cuando sea evidente. Devuelve solo la traduccion.\n\n"
        f"{text[:9000]}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
    }
    models = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
    for key in keys:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                res = requests.post(url, json=payload, timeout=45)
                if res.status_code in (429, 403):
                    continue
                res.raise_for_status()
                data = res.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                translated = "".join(part.get("text", "") for part in parts).strip()
                if translated:
                    return translated
            except Exception:
                continue
    return ""


def translate_text(text):
    if not text.strip():
        return ""
    chunks = []
    current = []
    current_len = 0
    for line in text.splitlines():
        if current_len + len(line) > 3500 and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("\n".join(current))
    translated = []
    translator = GoogleTranslator(source="auto", target="es")
    for chunk in chunks[:4]:
        try:
            translated.append(translator.translate(chunk))
        except Exception:
            translated.append("[traduccion pendiente] " + chunk)
    return "\n".join(translated)


def translate_text_latam(env, text):
    translated = translate_text_gemini(env, text)
    if translated:
        return translated
    return translate_text(text)


def title_and_summary_es(title, objectives, score):
    title_es = translate_text(title) if title else "Conversacion exitosa de Reddit"
    obj = ", ".join(objectives) if objectives else "conexion/humor"
    summary = (
        f"Sirve para Natalia porque contiene señales de {obj}, tiene OCR conversacional "
        f"y obtuvo un score heuristico de {score}/10 segun objetivo, conexion y calidad del abridor."
    )
    return title_es, summary


def save_candidate(conn, item):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO reddit_success_scrape_candidates (
            post_id, source_url, title, title_es, subreddit, image_urls_json,
            local_paths_json, ocr_text, ocr_lines_json, translation_es,
            objectives_json, score, summary_es, status, bytes_downloaded,
            discovery_source, category, image_hash, ocr_hash, error_message,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            source_url=excluded.source_url,
            title=excluded.title,
            title_es=excluded.title_es,
            subreddit=excluded.subreddit,
            image_urls_json=excluded.image_urls_json,
            local_paths_json=excluded.local_paths_json,
            ocr_text=excluded.ocr_text,
            ocr_lines_json=excluded.ocr_lines_json,
            translation_es=excluded.translation_es,
            objectives_json=excluded.objectives_json,
            score=excluded.score,
            summary_es=excluded.summary_es,
            status=excluded.status,
            bytes_downloaded=excluded.bytes_downloaded,
            discovery_source=excluded.discovery_source,
            category=excluded.category,
            image_hash=excluded.image_hash,
            ocr_hash=excluded.ocr_hash,
            error_message=excluded.error_message,
            updated_at=excluded.updated_at
        """,
        (
            item["post_id"],
            item["source_url"],
            item["title"],
            item["title_es"],
            item["subreddit"],
            json.dumps(item["image_urls"], ensure_ascii=False),
            json.dumps(item["local_paths"], ensure_ascii=False),
            item["ocr_text"],
            json.dumps(item["ocr_lines"], ensure_ascii=False),
            item["translation_es"],
            json.dumps(item["objectives"], ensure_ascii=False),
            item["score"],
            item["summary_es"],
            item["status"],
            item["bytes_downloaded"],
            item["discovery_source"],
            item.get("category", ""),
            item.get("image_hash", ""),
            item.get("ocr_hash", ""),
            item.get("error_message", ""),
            now,
            now,
        ),
    )
    conn.commit()


def failure_item(post_id, source_url, title, subreddit, status, error_message):
    return {
        "post_id": post_id,
        "source_url": source_url,
        "title": title,
        "title_es": title,
        "subreddit": subreddit,
        "image_urls": [],
        "local_paths": [],
        "ocr_text": "",
        "ocr_lines": [],
        "translation_es": "",
        "objectives": [],
        "score": 0,
        "summary_es": "",
        "status": status,
        "bytes_downloaded": 0,
        "discovery_source": "rss_decodo_proxy",
        "category": "fallo_tecnico",
        "image_hash": "",
        "ocr_hash": "",
        "error_message": str(error_message)[:500],
    }


def write_reports(run_label, rows, meter):
    DOCS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    html_path = DOCS_DIR / f"reddit_success_{run_label}.html"
    csv_path = DOCS_DIR / f"reddit_success_{run_label}.csv"
    json_path = RAW_DIR / f"reddit_success_{run_label}.json"
    json_path.write_text(json.dumps({"meter": meter, "results": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "score", "objectives", "title_es", "source_url", "status"])
        for row in rows:
            writer.writerow([row["post_id"], row["score"], ",".join(row["objectives"]), row["title_es"], row["source_url"], row["status"]])
    cards = []
    for idx, row in enumerate(rows, 1):
        imgs = "".join(f"<img src='{html.escape(path)}' alt='captura reddit'>" for path in row["local_paths"])
        ocr = html.escape(row["ocr_text"][:2500])
        trans = html.escape(row["translation_es"][:2500])
        cards.append(
            f"""
            <article class="case">
              <h2>#{idx} · {html.escape(row['title_es'])}</h2>
              <div class="meta"><span>Score {row['score']}/10</span><span>{html.escape(', '.join(row['objectives']))}</span><span>{html.escape(row['subreddit'])}</span></div>
              <a href="{html.escape(row['source_url'])}" target="_blank" rel="noreferrer">Post original</a>
              <p>{html.escape(row['summary_es'])}</p>
              <div class="grid"><div class="imgs">{imgs}</div><div><h3>OCR</h3><pre>{ocr}</pre><h3>Español latino</h3><pre>{trans}</pre></div></div>
            </article>
            """
        )
    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Reddit success {run_label}</title>
<style>body{{font-family:Arial,sans-serif;background:#101116;color:#f7f8fc;margin:0}}header,main{{max-width:1180px;margin:auto;padding:24px}}.case{{background:#191c25;border:1px solid #303545;border-radius:8px;padding:18px;margin:18px 0}}.meta{{display:flex;gap:8px;flex-wrap:wrap}}.meta span{{background:#293044;border-radius:999px;padding:5px 9px;color:#d4dcf3}}a{{color:#58e0b2}}.grid{{display:grid;grid-template-columns:minmax(260px,420px) 1fr;gap:18px}}img{{max-width:100%;display:block;margin:0 0 12px;border-radius:8px}}pre{{white-space:pre-wrap;background:#11141d;padding:12px;border-radius:8px;max-height:420px;overflow:auto}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}</style></head>
<body><header><h1>Prueba Reddit success {run_label}</h1><p>Descubrimiento por Decodo/proxy, imagen por directo/DataImpulse fallback, OCR local RapidOCR, traducción LATAM fallback web. Requests: {meter['requests']}, bytes: {meter['bytes']}.</p></header><main>{''.join(cards)}</main></body></html>"""
    html_path.write_text(doc, encoding="utf-8")
    return {"html": str(html_path), "csv": str(csv_path), "json": str(json_path)}


def write_reports_v2(run_label, rows, meter):
    DOCS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    html_path = DOCS_DIR / f"reddit_success_{run_label}.html"
    csv_path = DOCS_DIR / f"reddit_success_{run_label}.csv"
    json_path = RAW_DIR / f"reddit_success_{run_label}.json"
    rows = sorted(rows, key=lambda row: (-int(row.get("score", 0)), row.get("category", ""), row.get("title_es", "")))
    json_path.write_text(json.dumps({"meter": meter, "results": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "score", "category", "objectives", "title_es", "source_url", "status"])
        for row in rows:
            writer.writerow([row["post_id"], row["score"], row.get("category", ""), ",".join(row["objectives"]), row["title_es"], row["source_url"], row["status"]])

    categories = sorted({row.get("category", "sin_categoria") for row in rows})
    category_options = "".join(f"<option value='{html.escape(cat)}'>{html.escape(cat.replace('_', ' '))}</option>" for cat in categories)
    category_counts = {}
    for row in rows:
        category = row.get("category", "sin_categoria")
        category_counts[category] = category_counts.get(category, 0) + 1
    stats = "".join(
        f"<span class='chip'>{html.escape(cat.replace('_', ' '))}: {count}</span>"
        for cat, count in sorted(category_counts.items())
    )

    cards = []
    for idx, row in enumerate(rows, 1):
        imgs = "".join(
            f"<a href='{html.escape(Path(path).as_posix())}' target='_blank' rel='noreferrer'>"
            f"<img src='{html.escape(Path(path).as_posix())}' alt='captura reddit {idx}'></a>"
            for path in row["local_paths"]
        )
        ocr = html.escape(row["ocr_text"][:4000])
        trans = html.escape(row["translation_es"][:4000])
        objectives = ", ".join(row["objectives"]) or "conexion/humor"
        category = row.get("category", "sin_categoria")
        search_text = html.escape(" ".join([row.get("title_es", ""), row.get("title", ""), objectives, row.get("translation_es", ""), row.get("ocr_text", "")]).lower())
        cards.append(
            f"""
            <article class="case" data-score="{row['score']}" data-category="{html.escape(category)}" data-search="{search_text}">
              <div class="case-header">
                <div>
                  <p class="eyebrow">#{idx} - {html.escape(category.replace('_', ' '))}</p>
                  <h2>{html.escape(row['title_es'])}</h2>
                </div>
                <strong class="score">{row['score']}/10</strong>
              </div>
              <div class="meta"><span>{html.escape(objectives)}</span><span>{html.escape(row['subreddit'])}</span><span>{len(row['local_paths'])} imagen(es)</span></div>
              <a class="source" href="{html.escape(row['source_url'])}" target="_blank" rel="noreferrer">Ver post original</a>
              <p class="summary">{html.escape(row['summary_es'])}</p>
              <div class="grid">
                <div>
                  <h3>Imagen original / carrusel</h3>
                  <div class="imgs">{imgs}</div>
                </div>
                <div>
                  <h3>Conversacion traducida a espanol latino</h3>
                  <pre>{trans}</pre>
                  <h3>OCR original</h3>
                  <pre>{ocr}</pre>
                </div>
              </div>
            </article>
            """
        )

    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Reddit success {run_label}</title>
<style>
:root{{color-scheme:dark;--bg:#101116;--panel:#191c25;--panel2:#11141d;--text:#f7f8fc;--muted:#a9b2c8;--accent:#ff426d;--line:#303545;--green:#58e0b2}}
*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;background:var(--bg);color:var(--text);margin:0}}header,main{{max-width:1220px;margin:auto;padding:24px}}h1{{margin-bottom:8px}}.toolbar{{position:sticky;top:0;z-index:5;background:rgba(16,17,22,.96);border-bottom:1px solid var(--line);padding:12px 24px}}.toolbar-inner{{max-width:1220px;margin:auto;display:grid;grid-template-columns:1fr 220px 160px;gap:10px}}input,select{{width:100%;background:#222635;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:11px 12px;font-size:15px}}.chip,.meta span{{background:#293044;border-radius:999px;padding:5px 9px;color:#d4dcf3;display:inline-block}}.stats{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}.case{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px;margin:18px 0}}.case-header{{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}}.eyebrow{{margin:0 0 4px;color:var(--muted);text-transform:uppercase;font-size:12px;letter-spacing:.06em}}h2{{margin:0 0 10px;font-size:22px}}.score{{background:var(--accent);border-radius:10px;padding:9px 11px;white-space:nowrap}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}}a.source{{color:var(--green)}}.summary{{color:#d8deef}}.grid{{display:grid;grid-template-columns:minmax(280px,450px) 1fr;gap:18px;margin-top:14px}}.imgs{{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:8px}}.imgs a{{display:block;flex:0 0 auto;scroll-snap-align:start}}.imgs img{{max-width:100%;width:420px;max-height:680px;object-fit:contain;display:block;border-radius:8px;background:#090a0e}}pre{{white-space:pre-wrap;background:var(--panel2);padding:12px;border-radius:8px;max-height:420px;overflow:auto;line-height:1.45;overflow-wrap:anywhere}}.hidden{{display:none}}#empty{{display:none;color:var(--muted);padding:32px;text-align:center}}@media(max-width:800px){{.toolbar-inner{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr}}.case-header{{display:block}}.imgs img{{width:88vw}}}}
</style></head>
<body><header><h1>Prueba Reddit success {run_label}</h1><p>Ordenado por score de mejor a peor. Descubrimiento por Decodo/proxy, imagen directa con fallback DataImpulse, OCR local RapidOCR y traduccion LATAM fallback web. Requests: {meter['requests']}, bytes metadata: {meter['bytes']}, bytes imagenes: {meter.get('downloaded_bytes', 0)}.</p><div class="stats">{stats}</div></header>
<div class="toolbar"><div class="toolbar-inner"><input id="q" type="search" placeholder="Buscar por titulo, objetivo, OCR o traduccion..."><select id="cat"><option value="">Todas las categorias</option>{category_options}</select><select id="minScore"><option value="0">Score minimo</option><option value="10">10</option><option value="9">9+</option><option value="8">8+</option><option value="7">7+</option><option value="6">6+</option></select></div></div>
<main id="cases">{''.join(cards)}<div id="empty">No hay casos con esos filtros.</div></main>
<script>
function applyFilters(){{
  const q = document.getElementById('q').value.trim().toLowerCase();
  const cat = document.getElementById('cat').value;
  const minScore = Number(document.getElementById('minScore').value || 0);
  let visible = 0;
  document.querySelectorAll('.case').forEach(card => {{
    const okQ = !q || card.dataset.search.includes(q);
    const okCat = !cat || card.dataset.category === cat;
    const okScore = Number(card.dataset.score || 0) >= minScore;
    const show = okQ && okCat && okScore;
    card.classList.toggle('hidden', !show);
    if (show) visible += 1;
  }});
  document.getElementById('empty').style.display = visible ? 'none' : 'block';
}}
document.getElementById('q').addEventListener('input', applyFilters);
document.getElementById('cat').addEventListener('change', applyFilters);
document.getElementById('minScore').addEventListener('change', applyFilters);
</script></body></html>"""
    html_path.write_text(doc, encoding="utf-8")
    return {"html": str(html_path), "csv": str(csv_path), "json": str(json_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-requests", type=int, default=120)
    parser.add_argument("--run-label", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    env = read_env()
    conn = ensure_db()
    seen = existing_ids(conn)
    seen_hashes = existing_hashes(conn)
    engine = RapidOCR()
    session = requests.Session()
    meter = {"requests": 0, "bytes": 0, "downloaded_bytes": 0}
    accepted = []

    for subreddit in SUBREDDITS:
        for query in QUERIES:
            query_for_fetch = media_first_query(query)
            if len(accepted) >= args.limit or meter["requests"] >= args.max_requests:
                break
            try:
                xml_text, size = fetch_rss(session, env, subreddit, query_for_fetch)
                meter["requests"] += 1
                meter["bytes"] += size
            except Exception as exc:
                print(f"WARN rss {subreddit} {query_for_fetch}: {exc}", flush=True)
                continue
            for entry in parse_entries(xml_text):
                if len(accepted) >= args.limit:
                    break
                post_id = entry["post_id"]
                if not post_id or post_id in seen or not entry["image_urls"]:
                    continue
                try:
                    local_paths = []
                    downloaded = 0
                    source_used = []
                    for idx, img_url in enumerate(entry["image_urls"][:4], 1):
                        path, size, source = download_image(session, env, post_id, img_url, idx)
                        local_paths.append(str(path))
                        downloaded += size
                        source_used.append(source)
                    ocr_text, ocr_lines = run_ocr(engine, [Path(p) for p in local_paths])
                    image_hash = combined_image_hash(local_paths)
                    ocr_hash = normalized_text_hash(ocr_text)
                    objectives = detect_objectives(entry["title"], ocr_text)
                    score = score_case(entry["title"], ocr_text, objectives, len(ocr_lines))
                    category = classify_case(objectives, entry["title"], ocr_text, len(ocr_lines))
                    if image_hash in seen_hashes["image"] or (ocr_hash and ocr_hash in seen_hashes["ocr"]):
                        status = "duplicate_content"
                    elif has_negative_outcome(entry["title"], ocr_text):
                        status = "rejected_negative_outcome"
                    elif score < 6 or len(ocr_lines) < 5:
                        status = "rejected_low_score"
                    else:
                        status = "candidate_qa"
                    title_es, summary_es = title_and_summary_es(entry["title"], objectives, score)
                    translation_es = translate_text_latam(env, ocr_text) if status == "candidate_qa" else ""
                    item = {
                        "post_id": post_id,
                        "source_url": entry["url"],
                        "title": entry["title"],
                        "title_es": title_es,
                        "subreddit": subreddit,
                        "image_urls": entry["image_urls"],
                        "local_paths": local_paths,
                        "ocr_text": ocr_text,
                        "ocr_lines": ocr_lines,
                        "translation_es": translation_es,
                        "objectives": objectives,
                        "score": score,
                        "summary_es": summary_es,
                        "status": status,
                        "bytes_downloaded": downloaded,
                        "discovery_source": f"rss_decodo_proxy/image_{'+'.join(source_used)}",
                        "category": category,
                        "image_hash": image_hash,
                        "ocr_hash": ocr_hash,
                        "error_message": "",
                    }
                    save_candidate(conn, item)
                    seen.add(post_id)
                    meter["downloaded_bytes"] += downloaded
                    if status == "candidate_qa":
                        seen_hashes["image"].add(image_hash)
                        if ocr_hash:
                            seen_hashes["ocr"].add(ocr_hash)
                        accepted.append(item)
                        print(f"OK {len(accepted)}/{args.limit} {post_id} score={score} category={category} objectives={objectives}", flush=True)
                    else:
                        print(f"SKIP {status} {post_id} score={score}", flush=True)
                except Exception as exc:
                    try:
                        save_candidate(conn, failure_item(post_id, entry["url"], entry["title"], subreddit, "candidate_failed", exc))
                    except Exception:
                        pass
                    print(f"WARN candidate {post_id}: {exc}", flush=True)
        if len(accepted) >= args.limit or meter["requests"] >= args.max_requests:
            break
    paths = write_reports_v2(args.run_label, accepted, meter)
    print(json.dumps({"accepted": len(accepted), "meter": meter, "paths": paths}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
