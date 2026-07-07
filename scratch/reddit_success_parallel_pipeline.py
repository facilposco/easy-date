import argparse
import json
import random
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from rapidocr_onnxruntime import RapidOCR

from reddit_success_image_pipeline import (
    BROAD_SUCCESS_QUERIES,
    DB_PATH,
    DOCS_DIR,
    MULTILINGUAL_QUERIES,
    NEGATIVE_TERMS,
    OBJECTIVE_TERMS,
    QUALITY_TERMS,
    QUERIES,
    SUBREDDITS,
    classify_case,
    combined_image_hash,
    detect_objectives,
    download_image,
    ensure_db,
    existing_hashes,
    existing_ids,
    failure_item,
    fetch_rss,
    fetch_post_score,
    has_negative_outcome,
    normalized_text_hash,
    parse_entries,
    read_env,
    run_ocr,
    save_candidate,
    score_case,
    media_first_query,
    title_and_summary_es,
    translate_text_latam,
    write_reports_v2,
)


DB_LOCK = threading.Lock()
HASH_LOCK = threading.Lock()
TRANSLATE_LOCK = threading.Lock()
PROGRESS_LOCK = threading.Lock()
THREAD_LOCAL = threading.local()
SEARCH_MODES = [
    ("top", "all"),
    ("relevance", "all"),
    ("comments", "all"),
    ("new", "all"),
    ("top", "year"),
]
LOW_SIGNAL_SUBREDDITS = {"TinderSuccess"}
GLOBAL_SEARCH_SUBREDDITS = ["__global__"]
GLOBAL_APP_SEARCH_SUBREDDITS = ["__global_app__"]
APP_QUERY_SUBREDDITS = {
    "tinder": {"tinder", "tinderpickuplines", "tindersuccess"},
    "bumble": {"bumble"},
    "hinge": {"hingeapp"},
    "okcupid": {"okcupid"},
}
HIGH_SIGNAL_SUBREDDITS = [
    "Tinder",
    "Bumble",
    "OkCupid",
    "Tinderpickuplines",
    "hingeapp",
    "DatingApps",
    "OnlineDating",
]
EXTRA_SUCCESS_QUERIES = [
    "tinder she gave me her phone",
    "bumble she gave me her phone",
    "hinge she gave me her phone",
    "tinder got her digits",
    "bumble got her digits",
    "hinge got her digits",
    "tinder got her whatsapp",
    "bumble got her whatsapp",
    "hinge got her whatsapp",
    "tinder asked for my number",
    "bumble asked for my number",
    "hinge asked for my number",
    "tinder agreed to drinks",
    "bumble agreed to drinks",
    "hinge agreed to drinks",
    "tinder agreed to coffee",
    "bumble agreed to coffee",
    "hinge agreed to coffee",
    "tinder first date set",
    "bumble first date set",
    "hinge first date set",
    "tinder gave me snap",
    "bumble gave me snap",
    "hinge gave me snap",
]
HIGHYIELD_EXACT_QUERIES = [
    "got her number",
    "she gave me her number",
    "exchanged numbers",
    "asks for my number",
    "ask for a number",
    "got her whatsapp",
    "got her snap",
    "got her snapchat",
    "got her instagram",
    "moved to text",
    "phone number ensued",
    "number ensued",
    "asked for my number",
    "gave me her number",
    "gave me her snap",
    "gave me her instagram",
    "agreed to drinks",
    "agreed to coffee",
    "agreed to meet",
    "going on a date",
    "set up a date",
    "set up our first date",
    "secured a date",
    "date tonight",
    "first date set",
    "she said yes",
    "meeting up",
    "went on a date",
    "opener worked",
    "made her laugh",
    "conversation went well",
]
WINNER_TITLE_EXACT_QUERIES = [
    "got her phone number",
    "got her number and a date",
    "number and a date",
    "got the number",
    "got a phone number",
    "got me a phone number",
    "phone number and a date",
    "got me a phone number and a date",
    "got my first number",
    "exchanged phone numbers",
    "asked me for my number",
    "she asked for my number",
    "number in 3 texts",
    "gave me her number",
    "got her number",
    "got her digits",
    "got her whatsapp",
    "got her snapchat",
    "got her snap",
    "got her instagram",
    "gave me her snap",
    "gave me her instagram",
    "got a date",
    "got a date this week",
    "date this week",
    "date for this weekend",
    "date tomorrow",
    "date tonight",
    "first date set",
    "set up first date",
    "set up a date",
    "asked her out",
    "she said yes",
    "coffee date",
    "drinks date",
    "agreed to drinks",
    "agreed to coffee",
    "agreed to meet",
    "meeting up",
    "went on a date",
    "this went smoothly",
    "went smoothly",
    "too smoothly",
    "actually worked",
    "it worked",
    "worked for me tonight",
    "opener worked",
    "line worked",
    "pickup line worked",
    "made her laugh",
    "rizz",
]
APP_CONTEXT_TERMS = [
    "tinder",
    "bumble",
    "hinge",
    "okcupid",
    "okc",
    "grindr",
    "badoo",
    "happn",
    "dating app",
    "online dating",
]
NON_CHAT_OCR_TERMS = [
    "app won't work",
    "this app won't work",
    "similar apps",
    "edit profile",
    "smart photos",
    "quick about me tips",
    "bumble date",
    "prompts",
    "opening move",
    "opening moves",
    "write a fun and punchy intro",
    "let people know what it's like to date you",
    "looking for",
    "long-term partner",
    "aboutme",
    "about me",
    "send a compliment",
    "login with google",
    "loginwithgoogle",
    "login with facebook",
    "loginwithfacebook",
    "login with phone",
    "loginwithphone",
    "trouble logging in",
    "install",
    "download",
]
CHAT_EVIDENCE_TERMS = [
    "message",
    "messages",
    "sent",
    "delivered",
    "received",
    "reply",
    "replied",
    "texted",
    "chat",
    "conversation",
    "you matched",
    "youmatched",
    "matched with",
    "type a message",
    "write a message",
    "mensaje",
    "mensajes",
    "enviado",
    "enviada",
    "responder",
    "mensagem",
    "mensagens",
    "envio",
    "messaggio",
    "messaggi",
    "inviato",
    "rispondi",
    "gesendet",
    "nachricht",
    "nachrichten",
    "senden",
]
NON_DATING_CONTEXT_TERMS = [
    "linkedin",
    "lead generation",
    "business",
    "professional",
    "networking",
    "manager",
    "collaboration",
    "collaborazioni",
    "servizi",
]
SUCCESS_SIGNAL_TERMS = [
    "yes",
    "yess",
    "yesss",
    "sure",
    "sounds good",
    "sounds great",
    "i'm down",
    "im down",
    "i am down",
    "would love",
    "love to go out",
    "go out sometime",
    "we could",
    "we should",
    "let's",
    "lets",
    "definitely",
    "absolutely",
    "my snap is",
    "add me",
    "hit me up",
    "text me",
    "textme",
    "call me",
    "i'll call",
    "ill call",
    "i'll text",
    "ill text",
    "my number",
    "ur #",
    "whatsapp",
    "snapchat",
    "instagram",
    "insta",
    "haha",
    "hahaha",
    "lol",
    "lmao",
    "tomorrow's good",
    "tomorrows good",
    "drinkssoundsgreat",
    "tomorrow'sgood",
    "tomorrowsgood",
]
CONTACT_CLOSE_TERMS = [
    "my number",
    "my phone number",
    "my snap",
    "my snapchat",
    "my instagram",
    "my insta",
    "my ig",
    "my whatsapp",
    "here's my",
    "heres my",
    "text me",
    "call me",
    "add me",
    "snap is",
    "insta is",
    "instagram is",
    "whatsapp me",
    "textme",
]
DATE_CLOSE_TERMS = [
    "sure",
    "sounds good",
    "sounds great",
    "drinkssoundsgreat",
    "let's do it",
    "lets do it",
    "let'sgetbrunch",
    "letsgetbrunch",
    "i'm down",
    "im down",
    "i am down",
    "i agree",
    "would love",
    "definitely",
    "absolutely",
    "works for me",
    "see you",
    "tomorrow's good",
    "tomorrows good",
    "tomorrow'sgood",
    "tomorrowsgood",
]
TITLE_SUCCESS_TERMS = [
    "got her number",
    "got me a phone number",
    "phone number and a date",
    "got me a phone number and a date",
    "she gave me her number",
    "gave me her number",
    "got her whatsapp",
    "got her snap",
    "got her snapchat",
    "got her instagram",
    "gave me her snap",
    "gave me her instagram",
    "got a date",
    "secured a date",
    "date secured",
    "date this weekend",
    "date this week",
    "we have a date",
    "got asked out",
    "asked out",
    "first date set",
    "set up a date",
    "agreed to drinks",
    "agreed to coffee",
    "agreed to meet",
    "she said yes",
    "went on a date",
    "opener worked",
    "pickup line worked",
]
FAILURE_CONTEXT_TERMS = [
    "dick pic",
    "dick pics",
    "d*ck pic",
    "d*ck pics",
    "lost all interest",
    "go talk to one of them",
    "no ghosting",
    "letting her down",
    "didn't feel the spark",
    "didnt feel the spark",
    "not up to meeting",
    "not necessarily fully up to meeting",
    "banned from",
    "got banned",
    "what am i doing wrong",
    "coming on too strong",
    "got wrecked",
    "wrecked",
    "never heard from her again",
    "didn't work",
    "didnt work",
    "no response",
    "won't reply",
    "wont reply",
    "stops responding",
    "do not match me",
    "not going to speak",
    "wrong number",
    "not gonna reply",
    "not going to reply",
    "if you're not gonna reply",
    "if youre not gonna reply",
    "gimme grandma's number",
    "i would prefer to stay on here",
    "prefer to stay on here",
    "which is it",
    "got ghosted",
    "ghosted",
    "what should i have said",
    "is this normal",
    "kinda mean",
    "not a good line",
    "foot worship",
    "come to my apartment",
    "getting murdered",
    "jump your bones",
    "too sexy",
    "piss off",
    "got shot back",
    "don't mix colour",
    "dont mix colour",
    "not going to waste any more time",
    "waste any more time",
    "didn't really feel the chemistry",
    "didnt really feel the chemistry",
    "didn't feel the chemistry",
    "didnt feel the chemistry",
    "didn't feel a spark",
    "didnt feel a spark",
    "got mad",
    "good ass guy",
    "nice guy",
    "threatened me",
    "getting tired of this",
    "didn't feel the spark",
    "didnt feel the spark",
    "as friends",
    "stay friends",
    "would still love to stay",
    "i'm busy tonight",
    "im busy tonight",
    "busy tonight",
    "not sure how to respond",
    "what i'm doing",
    "what im doing",
    "unmatch",
    "unmatched",
    "icky",
    "i don't think we should see each other again",
    "i dont think we should see each other again",
    "didn't want to date",
    "didnt want to date",
    "cheap bumble",
    "access to someone's account",
    "access to someones account",
    "can't meet up",
    "cant meet up",
]
MULTILANG_HINTS = [
    "numero",
    "whatsapp",
    "consegui",
    "quedamos",
    "passou",
    "encontro",
    "donne",
    "rendez",
    "voir",
    "nummer",
    "treffen",
    "appuntamento",
    "vediamo",
]
LANGUAGE_PROBE_HINTS = {
    "de": ["nummer", "handynummer", "treffen", "ausgemacht", "erfolg"],
    "es": ["numero", "whatsapp", "cita", "quedamos", "salir", "funciono"],
    "pt": ["numero", "whatsapp", "encontro", "deu certo"],
    "fr": ["donne", "numero", "snap", "rendez", "voir"],
    "it": ["numero", "whatsapp", "appuntamento", "vediamo"],
}


def get_engine():
    engine = getattr(THREAD_LOCAL, "ocr_engine", None)
    if engine is None:
        engine = RapidOCR()
        THREAD_LOCAL.ocr_engine = engine
    return engine


def cheap_prefilter(entry, discovery_query="", subreddit="", strict=False):
    if not entry.get("image_urls"):
        return False, "sin_imagen"
    source_hay = f" {entry.get('title', '')} {entry.get('url', '')} ".lower()
    hay = f" {entry.get('title', '')} {discovery_query} ".lower()
    if any(term in hay for term in NEGATIVE_TERMS):
        return False, "titulo_negativo"
    positive_terms = []
    for terms in OBJECTIVE_TERMS.values():
        positive_terms.extend(terms)
    positive_terms.extend(QUALITY_TERMS)
    if str(subreddit).startswith("__global_app"):
        if not any(term in source_hay for term in APP_CONTEXT_TERMS):
            return False, "global_sin_app_en_titulo_url"
        if any(term in source_hay for term in positive_terms):
            return True, "global_titulo_url_positivo"
        if strict:
            return False, "global_sin_senal_objetivo"
    if any(term in hay for term in positive_terms):
        return True, "titulo_positivo"
    if strict:
        return False, "sin_senal_objetivo"
    if subreddit in LOW_SIGNAL_SUBREDDITS:
        return False, "subreddit_baja_senal_sin_objetivo"
    return True, "requiere_ocr"


def has_app_context(entry, subreddit, ocr_text):
    hay = " ".join(
        [
            subreddit or "",
            entry.get("url", "") or "",
            entry.get("title", "") or "",
            ocr_text or "",
        ]
    ).lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", hay) for term in APP_CONTEXT_TERMS)


def contains_term(hay, term):
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", hay))


def has_objective_in_ocr(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    for terms in OBJECTIVE_TERMS.values():
        if any(contains_term(hay, term) for term in terms):
            return True
    return False


def has_app_source_or_chat_evidence(entry, subreddit, ocr_text):
    source_hay = " ".join([subreddit or "", entry.get("url", "") or "", entry.get("title", "") or ""]).lower()
    if any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", source_hay) for term in APP_CONTEXT_TERMS):
        return True
    ocr_hay = f" {ocr_text or ''} ".lower()
    return any(contains_term(ocr_hay, term) for term in CHAT_EVIDENCE_TERMS)


def has_chat_evidence(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    return any(contains_term(hay, term) for term in CHAT_EVIDENCE_TERMS)


def has_non_dating_context(entry, subreddit, ocr_text):
    hay = " ".join(
        [
            subreddit or "",
            entry.get("url", "") or "",
            entry.get("title", "") or "",
            ocr_text or "",
        ]
    ).lower()
    return any(term in hay for term in NON_DATING_CONTEXT_TERMS)


def has_failure_context(entry, ocr_text):
    hay = f" {entry.get('title', '') or ''} {ocr_text or ''} ".lower()
    return any(term in hay for term in FAILURE_CONTEXT_TERMS)


def has_success_signal(entry, ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    return any(contains_term(hay, term) for term in SUCCESS_SIGNAL_TERMS)


def has_contact_close(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    if re.search(r"(?<!\d)(?:\+?\d[\d .()\-]{6,}\d)(?!\d)", hay):
        return True
    return any(contains_term(hay, term) for term in CONTACT_CLOSE_TERMS)


def has_date_close(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    has_plan = any(contains_term(hay, term) for term in OBJECTIVE_TERMS.get("cita", []))
    has_acceptance = any(contains_term(hay, term) for term in DATE_CLOSE_TERMS)
    return has_plan and has_acceptance


def has_verified_outcome(objectives, ocr_text):
    objective_set = set(objectives)
    if objective_set & {"telefono", "whatsapp", "instagram", "snapchat"}:
        return has_contact_close(ocr_text)
    if "cita" in objective_set:
        return has_date_close(ocr_text)
    return False


def title_claims_success(entry, ocr_text):
    title = f" {entry.get('title', '') or ''} ".lower()
    if not any(contains_term(title, term) for term in TITLE_SUCCESS_TERMS):
        return False
    return has_chat_evidence(ocr_text) and not has_failure_context(entry, ocr_text)


def looks_like_non_chat_screen(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    if not any(term in hay for term in NON_CHAT_OCR_TERMS):
        return False
    return not any(term in hay for term in ["message", "messages", "sent", "received", "reply"])


def looks_like_profile_screen(ocr_text):
    hay = f" {ocr_text or ''} ".lower()
    profile_terms = [
        "edit profile",
        "smart photos",
        "quick about me tips",
        "about me",
        "aboutme",
        "bumble date",
        "prompts",
        "opening move",
        "opening moves",
        "write a fun and punchy intro",
        "let people know what it's like to date you",
        "looking for",
        "long-term partner",
        "send a compliment",
    ]
    chat_terms = ["you matched", "youmatched", "send a message", "type a message", "sent"]
    return any(term in hay for term in profile_terms) and not any(term in hay for term in chat_terms)


def status_counts():
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_rejected_audit(conn)
        main_rows = conn.execute(
            """
            SELECT status, COUNT(*)
            FROM reddit_success_scrape_candidates
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
        audit_rows = conn.execute(
            """
            SELECT status, COUNT(*)
            FROM reddit_success_scrape_rejected_audit
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
        counts = {status: count for status, count in audit_rows}
        counts.update({status: count for status, count in main_rows})
        return counts
    finally:
        conn.close()


def ensure_rejected_audit(conn):
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
    conn.commit()


def existing_audit_ids(conn):
    ensure_rejected_audit(conn)
    rows = conn.execute("SELECT post_id FROM reddit_success_scrape_rejected_audit").fetchall()
    return {row[0] for row in rows if row and row[0]}


def save_rejected_audit(conn, item):
    ensure_rejected_audit(conn)
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO reddit_success_scrape_rejected_audit (
            post_id, source_url, title, subreddit, image_urls_json,
            local_paths_json, ocr_text, ocr_lines_json, objectives_json,
            score, status, bytes_downloaded, discovery_source, category,
            image_hash, ocr_hash, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            source_url=excluded.source_url,
            title=excluded.title,
            subreddit=excluded.subreddit,
            image_urls_json=excluded.image_urls_json,
            local_paths_json=excluded.local_paths_json,
            ocr_text=excluded.ocr_text,
            ocr_lines_json=excluded.ocr_lines_json,
            objectives_json=excluded.objectives_json,
            score=excluded.score,
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
            item["subreddit"],
            json.dumps(item["image_urls"], ensure_ascii=False),
            json.dumps(item["local_paths"], ensure_ascii=False),
            item["ocr_text"],
            json.dumps(item["ocr_lines"], ensure_ascii=False),
            json.dumps(item["objectives"], ensure_ascii=False),
            item["score"],
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


def save_item(item):
    with DB_LOCK:
        conn = ensure_db()
        try:
            ensure_rejected_audit(conn)
            if item.get("status") == "candidate_qa":
                save_candidate(conn, item)
            else:
                save_rejected_audit(conn, item)
        finally:
            conn.close()


def process_entry(entry, subreddit, env, seen_hashes, args):
    post_id = entry["post_id"]
    session = requests.Session()
    try:
        local_paths = []
        downloaded = 0
        source_used = []
        for idx, img_url in enumerate(entry["image_urls"][: args.max_images_per_post], 1):
            path, size, source = download_image(session, env, post_id, img_url, idx)
            local_paths.append(str(path))
            downloaded += size
            source_used.append(source)

        ocr_text, ocr_lines = run_ocr(get_engine(), [Path(path) for path in local_paths])
        image_hash = combined_image_hash(local_paths)
        ocr_hash = normalized_text_hash(ocr_text)
        objectives = detect_objectives(entry["title"], ocr_text)
        score = score_case(entry["title"], ocr_text, objectives, len(ocr_lines))
        category = classify_case(objectives, entry["title"], ocr_text, len(ocr_lines))

        with HASH_LOCK:
            duplicate = image_hash in seen_hashes["image"] or (ocr_hash and ocr_hash in seen_hashes["ocr"])
            if not duplicate:
                seen_hashes["image"].add(image_hash)
                if ocr_hash:
                    seen_hashes["ocr"].add(ocr_hash)

        if duplicate:
            status = "duplicate_content"
        elif has_negative_outcome(entry["title"], ocr_text):
            status = "rejected_negative_outcome"
        elif has_failure_context(entry, ocr_text):
            status = "rejected_negative_outcome"
        elif is_global_search_subreddit(subreddit) and has_non_dating_context(entry, subreddit, ocr_text):
            status = "rejected_low_score"
        elif is_global_search_subreddit(subreddit) and not has_app_context(entry, subreddit, ocr_text):
            status = "rejected_low_score"
        elif is_global_search_subreddit(subreddit) and not has_app_source_or_chat_evidence(entry, subreddit, ocr_text):
            status = "rejected_low_score"
        elif is_global_search_subreddit(subreddit) and not has_objective_in_ocr(ocr_text) and not title_claims_success(entry, ocr_text):
            status = "rejected_low_score"
        elif is_global_search_subreddit(subreddit) and looks_like_non_chat_screen(ocr_text):
            status = "rejected_low_score"
        elif looks_like_profile_screen(ocr_text):
            status = "rejected_low_score"
        elif not has_chat_evidence(ocr_text):
            status = "rejected_low_score"
        elif not has_success_signal(entry, ocr_text):
            status = "rejected_low_score"
        elif not (has_verified_outcome(objectives, ocr_text) or title_claims_success(entry, ocr_text)):
            status = "rejected_low_score"
        elif score < args.min_score or len(ocr_lines) < args.min_ocr_lines:
            status = "rejected_low_score"
        else:
            status = "candidate_qa"

        title_es, summary_es = title_and_summary_es(entry["title"], objectives, score)
        translation_es = ""
        if status == "candidate_qa" and not args.defer_translation:
            with TRANSLATE_LOCK:
                translation_es = translate_text_latam(env, ocr_text)

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
            "discovery_source": f"parallel_rss_decodo_proxy/image_{'+'.join(source_used)}",
            "category": category,
            "image_hash": image_hash,
            "ocr_hash": ocr_hash,
            "error_message": "",
        }
        save_item(item)
        return item
    except Exception as exc:
        item = failure_item(post_id, entry.get("url", ""), entry.get("title", ""), subreddit, "candidate_failed", exc)
        item["discovery_source"] = "parallel_rss_decodo_proxy"
        save_item(item)
        return item
    finally:
        session.close()


def process_batch(batch, env, seen_hashes, args, accepted, meter):
    if not batch:
        return
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_entry, entry, subreddit, env, seen_hashes, args) for subreddit, entry in batch]
        for future in as_completed(futures):
            item = future.result()
            with PROGRESS_LOCK:
                meter["downloaded_bytes"] += int(item.get("bytes_downloaded") or 0)
                if item["status"] == "candidate_qa":
                    accepted.append(item)
                    print(
                        f"OK {len(accepted)}/{args.limit} {item['post_id']} "
                        f"score={item['score']} category={item.get('category', '')} "
                        f"objectives={item.get('objectives', [])}",
                        flush=True,
                    )
                else:
                    print(f"SKIP {item['status']} {item['post_id']} score={item.get('score', 0)}", flush=True)
                if len(accepted) % max(1, args.progress_every) == 0 and item["status"] == "candidate_qa":
                    print(f"STATUS accepted={len(accepted)} counts={json.dumps(status_counts(), ensure_ascii=False)}", flush=True)


class RateLimiter:
    def __init__(self, rate_per_second):
        self.interval = 1.0 / max(0.1, rate_per_second)
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_at:
                time.sleep(self.next_at - now)
                now = time.monotonic()
            self.next_at = now + self.interval


def queries_for_profile(profile):
    if profile == "top_media_highsignal":
        return ["self:no"]
    if profile == "winner_title_exact":
        app_queries = []
        for app in ["tinder", "bumble", "hinge", "okcupid"]:
            app_queries.extend(f"{app} {query}" for query in WINNER_TITLE_EXACT_QUERIES)
        return list(dict.fromkeys(app_queries + WINNER_TITLE_EXACT_QUERIES + HIGHYIELD_EXACT_QUERIES))
    if profile == "global_app_exact":
        app_queries = []
        for app in ["tinder", "bumble", "hinge", "okcupid"]:
            app_queries.extend(f"{app} {query}" for query in HIGHYIELD_EXACT_QUERIES)
        return list(dict.fromkeys(app_queries + EXTRA_SUCCESS_QUERIES))
    if profile == "global_exact":
        return list(dict.fromkeys(HIGHYIELD_EXACT_QUERIES + EXTRA_SUCCESS_QUERIES))
    if profile == "highyield_exact":
        app_queries = []
        for app in ["tinder", "bumble", "hinge", "okcupid"]:
            app_queries.extend(f"{app} {query}" for query in HIGHYIELD_EXACT_QUERIES)
        return list(dict.fromkeys(app_queries + EXTRA_SUCCESS_QUERIES + HIGHYIELD_EXACT_QUERIES))
    if profile not in {"multilang_deep", "multilang_global"}:
        return QUERIES
    multilang_broad = [
        query for query in BROAD_SUCCESS_QUERIES
        if any(hint in query.lower() for hint in MULTILANG_HINTS)
    ]
    return list(dict.fromkeys(EXTRA_SUCCESS_QUERIES + multilang_broad + MULTILINGUAL_QUERIES + QUERIES))


def subreddits_for_profile(profile, include_low_signal=False):
    base = SUBREDDITS if include_low_signal else [s for s in SUBREDDITS if s not in LOW_SIGNAL_SUBREDDITS]
    if profile == "top_media_highsignal":
        return HIGH_SIGNAL_SUBREDDITS
    if profile == "winner_title_exact":
        return ["Tinder", "Bumble", "hingeapp", "OkCupid", "Tinderpickuplines"]
    if profile == "global_app_exact":
        return GLOBAL_APP_SEARCH_SUBREDDITS
    if profile == "global_exact":
        return list(dict.fromkeys(GLOBAL_SEARCH_SUBREDDITS + HIGH_SIGNAL_SUBREDDITS))
    if profile == "highyield_exact":
        return HIGH_SIGNAL_SUBREDDITS
    if profile == "multilang_global":
        return list(dict.fromkeys(HIGH_SIGNAL_SUBREDDITS + [s for s in base if s not in HIGH_SIGNAL_SUBREDDITS] + GLOBAL_SEARCH_SUBREDDITS))
    return base


def is_multilang_query(query):
    lowered = query.lower()
    return any(hint in lowered for hint in MULTILANG_HINTS) or query in MULTILINGUAL_QUERIES


def filter_queries_for_language(queries, language_probe):
    if language_probe == "all":
        return queries
    if language_probe == "en":
        return [query for query in queries if not is_multilang_query(query)]
    hints = LANGUAGE_PROBE_HINTS.get(language_probe, [])
    filtered = [
        query for query in queries
        if any(hint in str(query).lower() for hint in hints)
    ]
    return filtered or queries


def is_global_search_subreddit(subreddit):
    return str(subreddit).startswith("__global")


def query_matches_subreddit(query, subreddit):
    subreddit_key = str(subreddit).lower()
    query_key = str(query).lower().strip().strip('"')
    for app, allowed_subreddits in APP_QUERY_SUBREDDITS.items():
        if query_key.startswith(app + " "):
            return is_global_search_subreddit(subreddit) or subreddit_key in allowed_subreddits
    return True


def discovery_jobs(include_low_signal=False, queries=None, subreddits=None):
    query_list = queries or QUERIES
    subreddits = subreddits or subreddits_for_profile("default", include_low_signal)
    for subreddit in subreddits:
        subreddit_queries = [query for query in query_list if is_multilang_query(query)] if subreddit in GLOBAL_SEARCH_SUBREDDITS else query_list
        for query in subreddit_queries:
            if not query_matches_subreddit(query, subreddit):
                continue
            query_for_fetch = media_first_query(query)
            for sort, time_window in SEARCH_MODES:
                yield subreddit, query_for_fetch, sort, time_window


def fetch_discovery(job, env, limiter):
    subreddit, query_for_fetch, sort, time_window = job
    limiter.wait()
    session = requests.Session()
    try:
        xml_text, size = fetch_rss(session, env, subreddit, query_for_fetch, sort=sort, time_window=time_window)
        return {
            "ok": True,
            "subreddit": subreddit,
            "query": query_for_fetch,
            "sort": sort,
            "time_window": time_window,
            "xml_text": xml_text,
            "size": size,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "subreddit": subreddit,
            "query": query_for_fetch,
            "sort": sort,
            "time_window": time_window,
            "xml_text": "",
            "size": 0,
            "error": str(exc),
        }
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--max-requests", type=int, default=12000)
    parser.add_argument("--run-label", default="parallel_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-images-per-post", type=int, default=4)
    parser.add_argument("--min-reddit-score", type=int, default=0)
    parser.add_argument("--score-decodo-fallback", action="store_true")
    parser.add_argument("--score-dataimpulse-fallback", action="store_true")
    parser.add_argument("--min-score", type=int, default=6)
    parser.add_argument("--min-ocr-lines", type=int, default=5)
    parser.add_argument("--sleep-min", type=float, default=1.5)
    parser.add_argument("--sleep-max", type=float, default=4.0)
    parser.add_argument("--discovery-workers", type=int, default=16)
    parser.add_argument("--decodo-rps", type=float, default=9.0)
    parser.add_argument("--discovery-window", type=int, default=72)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--strict-title-prefilter", action="store_true")
    parser.add_argument("--include-low-signal-subreddits", action="store_true")
    parser.add_argument("--defer-translation", action="store_true")
    parser.add_argument("--query-profile", choices=["default", "multilang_deep", "multilang_global", "highyield_exact", "global_exact", "global_app_exact", "top_media_highsignal", "winner_title_exact"], default="default")
    parser.add_argument("--language-probe", choices=["all", "en", "es", "pt", "fr", "de", "it"], default="all")
    parser.add_argument("--early-stop-empty-windows", type=int, default=4)
    parser.add_argument("--early-stop-duplicate-windows", type=int, default=3)
    args = parser.parse_args()

    DOCS_DIR.mkdir(exist_ok=True)
    env = read_env()
    conn = ensure_db()
    try:
        ensure_rejected_audit(conn)
        seen_ids = existing_ids(conn) | existing_audit_ids(conn)
        seen_hashes = existing_hashes(conn)
        resume_counts = status_counts()
    finally:
        conn.close()

    accepted = []
    meter = {"requests": 0, "bytes": 0, "downloaded_bytes": 0}
    pending = []
    score_cache = {}
    skipped_prefilter = 0
    query_stats = {}
    disabled_query_keys = set()
    active_queries = filter_queries_for_language(queries_for_profile(args.query_profile), args.language_probe)
    active_subreddits = subreddits_for_profile(args.query_profile, args.include_low_signal_subreddits)

    print(
        json.dumps(
            {
                "event": "start",
                "run_label": args.run_label,
                "limit": args.limit,
                "workers": args.workers,
                "batch_size": args.batch_size,
                "discovery_workers": args.discovery_workers,
                "decodo_rps": args.decodo_rps,
                "discovery_window": args.discovery_window,
                "query_profile": args.query_profile,
                "language_probe": args.language_probe,
                "query_count": len(active_queries),
                "subreddit_count": len(active_subreddits),
                "resume_seen_ids": len(seen_ids),
                "resume_counts": resume_counts,
                "db": str(DB_PATH),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    def handle_entries(subreddit, query, sort, entries):
        nonlocal skipped_prefilter
        stats = {"seen": 0, "known": 0, "prefilter": 0, "enqueued": 0}
        for entry in entries:
            stats["seen"] += 1
            if len(accepted) >= args.limit:
                break
            post_id = entry["post_id"]
            if not post_id or post_id in seen_ids:
                stats["known"] += 1
                continue
            keep, reason = cheap_prefilter(
                entry,
                discovery_query=query,
                subreddit=subreddit,
                strict=args.strict_title_prefilter,
            )
            seen_ids.add(post_id)
            if not keep:
                stats["prefilter"] += 1
                skipped_prefilter += 1
                print(f"PREFILTER_SKIP {reason} {post_id}", flush=True)
                continue
            if args.min_reddit_score > 0:
                try:
                    if post_id not in score_cache:
                        score_session = requests.Session()
                        score_cache[post_id] = fetch_post_score(
                            score_session,
                            env,
                            post_id,
                            allow_decodo=args.score_decodo_fallback,
                            allow_dataimpulse=args.score_dataimpulse_fallback,
                        )
                        score_session.close()
                    reddit_score = score_cache.get(post_id)
                except Exception as exc:
                    print(f"PREFILTER_SKIP score_no_disponible {post_id}: {exc}", flush=True)
                    continue
                if reddit_score is None or reddit_score < args.min_reddit_score:
                    skipped_prefilter += 1
                    print(f"PREFILTER_SKIP score_bajo {post_id} score={reddit_score} min={args.min_reddit_score}", flush=True)
                    continue
            pending.append((subreddit, entry))
            stats["enqueued"] += 1
            if len(pending) >= args.batch_size:
                process_batch(pending, env, seen_hashes, args, accepted, meter)
                pending.clear()
                if len(accepted) >= args.limit:
                    break
        return stats

    def handle_discovery_result(result):
        nonlocal skipped_prefilter
        query_key = (result["subreddit"], result["query"])
        if not result["ok"]:
            print(
                f"WARN rss {result['subreddit']} {result['query']} "
                f"sort={result['sort']} t={result['time_window']}: {result['error']}",
                flush=True,
            )
            return
        meter["requests"] += 1
        meter["bytes"] += result["size"]
        print(
            f"DISCOVER {result['subreddit']} {result['query']} "
            f"sort={result['sort']} t={result['time_window']} "
            f"bytes={result['size']} requests={meter['requests']}",
            flush=True,
        )
        try:
            entries = list(parse_entries(result["xml_text"]))
        except Exception as exc:
            print(
                f"WARN parse {result['subreddit']} {result['query']} "
                f"sort={result['sort']} t={result['time_window']}: {exc}",
                flush=True,
            )
            return
        stats = handle_entries(result["subreddit"], result["query"], result["sort"], entries)
        current = query_stats.setdefault(query_key, {"empty": 0, "known_only": 0, "enqueued": 0})
        current["enqueued"] += stats["enqueued"]
        if stats["seen"] == 0 or stats["enqueued"] == 0:
            current["empty"] += 1
        if stats["seen"] > 0 and stats["known"] == stats["seen"]:
            current["known_only"] += 1
        if (
            current["empty"] >= args.early_stop_empty_windows
            or current["known_only"] >= args.early_stop_duplicate_windows
        ):
            disabled_query_keys.add(query_key)
            print(
                f"EARLY_STOP {result['subreddit']} {result['query']} "
                f"empty={current['empty']} known_only={current['known_only']} enqueued={current['enqueued']}",
                flush=True,
            )

    def next_enabled_job(jobs):
        for job in jobs:
            if (job[0], job[1]) in disabled_query_keys:
                continue
            return job
        raise StopIteration

    if args.discovery_workers > 1:
        limiter = RateLimiter(args.decodo_rps)
        jobs = iter(discovery_jobs(args.include_low_signal_subreddits, active_queries, active_subreddits))
        futures = set()
        with ThreadPoolExecutor(max_workers=args.discovery_workers) as executor:
            while len(futures) < args.discovery_window and meter["requests"] < args.max_requests:
                try:
                    futures.add(executor.submit(fetch_discovery, next_enabled_job(jobs), env, limiter))
                except StopIteration:
                    break
            while futures and len(accepted) < args.limit and meter["requests"] < args.max_requests:
                for future in as_completed(futures):
                    futures.remove(future)
                    handle_discovery_result(future.result())
                    break
                while (
                    len(futures) < args.discovery_window
                    and len(accepted) < args.limit
                    and meter["requests"] + len(futures) < args.max_requests
                ):
                    try:
                        futures.add(executor.submit(fetch_discovery, next_enabled_job(jobs), env, limiter))
                    except StopIteration:
                        break
    else:

        for subreddit in active_subreddits:
            subreddit_queries = [query for query in active_queries if is_multilang_query(query)] if subreddit in GLOBAL_SEARCH_SUBREDDITS else active_queries
            for query in subreddit_queries:
                if not query_matches_subreddit(query, subreddit):
                    continue
                query_for_fetch = media_first_query(query)
                for sort, time_window in SEARCH_MODES:
                    if (subreddit, query_for_fetch) in disabled_query_keys:
                        break
                    if len(accepted) >= args.limit or meter["requests"] >= args.max_requests:
                        break
                    try:
                        session = requests.Session()
                        xml_text, size = fetch_rss(session, env, subreddit, query_for_fetch, sort=sort, time_window=time_window)
                        session.close()
                        result = {
                            "ok": True,
                            "subreddit": subreddit,
                            "query": query_for_fetch,
                            "sort": sort,
                            "time_window": time_window,
                            "xml_text": xml_text,
                            "size": size,
                            "error": "",
                        }
                        handle_discovery_result(result)
                    except Exception as exc:
                        print(f"WARN rss {subreddit} {query_for_fetch} sort={sort} t={time_window}: {exc}", flush=True)
                        continue

                    time.sleep(random.uniform(args.sleep_min, args.sleep_max))
                if len(accepted) >= args.limit or meter["requests"] >= args.max_requests:
                    break

            if len(accepted) >= args.limit or meter["requests"] >= args.max_requests:
                break

    if pending and len(accepted) < args.limit:
        process_batch(pending, env, seen_hashes, args, accepted, meter)

    meter["skipped_prefilter"] = skipped_prefilter
    meter["disabled_query_keys"] = len(disabled_query_keys)
    paths = write_reports_v2(args.run_label, accepted, meter)
    print(
        json.dumps(
            {
                "event": "finish",
                "accepted": len(accepted),
                "meter": meter,
                "counts": status_counts(),
                "paths": paths,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
