import argparse
import html
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
RAW_DIR = ROOT / "scratch" / "reddit_dialogue_text_scan_raw"
DB_PATH = ROOT / "textgame.db"
MODEL = "gemini-2.0-flash-lite"


def latest_source():
    files = sorted(RAW_DIR.glob("reddit_dialogues_text_top10_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("No encontre JSON fuente en scratch/reddit_dialogue_text_scan_raw.")
    return files[0]


def load_keys():
    env_path = ROOT / ".env"
    keys = []
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.startswith("GEMINI_API_KEY") and "=" in raw:
            value = raw.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                keys.append(value)
    if not keys:
        raise SystemExit("No encontre GEMINI_API_KEY_* en .env.")
    return keys


def gemini_json(keys, payload):
    prompt = {
        "instruction": (
            "Traduce y corrige al espanol latino neutro este caso real de app de citas. "
            "No inventes informacion, no suavices el resultado, conserva el sentido emocional y el orden. "
            "Corrige ortografia y gramatica para que suene natural en Latinoamerica. "
            "Devuelve solo JSON valido con: title_es, context_es, quality_note_es, turns_es. "
            "turns_es debe tener la misma cantidad y orden de elementos que turns; cada elemento: "
            "{speaker, text_es}."
        ),
        "case": payload,
    }
    body = {
        "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    }
    last_error = None
    for attempt in range(6):
        key = keys[attempt % len(keys)]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
        try:
            response = requests.post(url, params={"key": key}, json=body, timeout=60)
            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = f"HTTP {response.status_code}"
                time.sleep(2 + attempt)
                continue
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as exc:
            last_error = str(exc)
            time.sleep(2 + attempt)
    raise RuntimeError(f"No se pudo traducir con Gemini: {last_error}")


def fallback_translation(item):
    return {
        "title_es": item["title"],
        "context_es": "Traduccion pendiente por bloqueo del modelo.",
        "quality_note_es": "No usar para entrenamiento hasta traducir y revisar manualmente.",
        "turns_es": [{"speaker": turn["speaker"], "text_es": turn["text"]} for turn in item["turns"]],
    }


def translate_items(source, keys):
    output = []
    for idx, item in enumerate(source["results"], 1):
        payload = {
            "title": item["title"],
            "subreddit": item["subreddit"],
            "body_excerpt": item.get("body", "")[:1800],
            "turns": [{"speaker": turn["speaker"], "text": turn["text"]} for turn in item["turns"]],
        }
        try:
            translated = gemini_json(keys, payload)
        except Exception as exc:
            translated = fallback_translation(item)
            translated["translation_error"] = str(exc)
        if len(translated.get("turns_es", [])) != len(item["turns"]):
            translated["turns_es"] = fallback_translation(item)["turns_es"]
            translated["quality_note_es"] = (
                translated.get("quality_note_es", "")
                + " Revision necesaria: el modelo no devolvio la misma cantidad de turnos."
            ).strip()
        output.append({**item, "translation": translated})
        print(f"Traducido {idx}/{len(source['results'])}: {item['post_id']}", flush=True)
    return output


def save_db(items):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reddit_dialogue_text_candidates (
                post_id TEXT PRIMARY KEY,
                subreddit TEXT,
                source_url TEXT,
                title_original TEXT,
                title_es TEXT,
                body_original TEXT,
                context_es TEXT,
                turns_original_json TEXT,
                turns_es_json TEXT,
                quality_score INTEGER,
                quality_note_es TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        now = datetime.now().isoformat(timespec="seconds")
        for item in items:
            tr = item["translation"]
            conn.execute(
                """
                INSERT INTO reddit_dialogue_text_candidates (
                    post_id, subreddit, source_url, title_original, title_es,
                    body_original, context_es, turns_original_json, turns_es_json,
                    quality_score, quality_note_es, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    subreddit=excluded.subreddit,
                    source_url=excluded.source_url,
                    title_original=excluded.title_original,
                    title_es=excluded.title_es,
                    body_original=excluded.body_original,
                    context_es=excluded.context_es,
                    turns_original_json=excluded.turns_original_json,
                    turns_es_json=excluded.turns_es_json,
                    quality_score=excluded.quality_score,
                    quality_note_es=excluded.quality_note_es,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (
                    item["post_id"],
                    item["subreddit"],
                    item["url"],
                    item["title"],
                    tr.get("title_es", item["title"]),
                    item.get("body", ""),
                    tr.get("context_es", ""),
                    json.dumps(item["turns"], ensure_ascii=False),
                    json.dumps(tr.get("turns_es", []), ensure_ascii=False),
                    item.get("quality_score", 0),
                    tr.get("quality_note_es", ""),
                    "candidato_traducido_latam",
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def write_html(items, source_path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = DOCS_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.html"
    json_path = RAW_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.json"
    csv_path = DOCS_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.csv"

    json_path.write_text(json.dumps({"source": str(source_path), "results": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        f.write("rank,post_id,subreddit,quality_score,title_es,status\\n")
        for rank, item in enumerate(items, 1):
            title = item["translation"].get("title_es", item["title"]).replace('"', '""')
            f.write(f'{rank},{item["post_id"]},{item["subreddit"]},{item["quality_score"]},"{title}",candidato_traducido_latam\\n')

    cards = []
    for rank, item in enumerate(items, 1):
        tr = item["translation"]
        turns = tr.get("turns_es", [])
        turns_html = "".join(
            f"<div class='turn {html.escape(turn.get('speaker', ''))}'><b>{'Hombre' if turn.get('speaker') == 'hombre' else 'Mujer'}</b><p>{html.escape(turn.get('text_es', ''))}</p></div>"
            for turn in turns
        )
        cards.append(
            f"""
            <article class="case">
              <div class="rank">#{rank}</div>
              <div class="meta">
                <span>r/{html.escape(item['subreddit'])}</span>
                <span>{len(turns)} turnos traducidos</span>
                <span>Score: {item['quality_score']}</span>
                <span>DB: candidato traducido</span>
              </div>
              <h2>{html.escape(tr.get('title_es', item['title']))}</h2>
              <a href="{html.escape(item['url'])}" target="_blank" rel="noreferrer">Abrir fuente original</a>
              <p class="context">{html.escape(tr.get('context_es', ''))}</p>
              <section class="dialogue">{turns_html}</section>
              <details><summary>Original en ingles</summary><p>{html.escape(item.get('body', '')[:2400])}</p></details>
              <p class="note">{html.escape(tr.get('quality_note_es', ''))}</p>
            </article>
            """
        )

    doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Easy Date - Dialogos Reddit traducidos LATAM</title>
  <style>
    body {{ margin:0; font-family: Arial, sans-serif; background:#101116; color:#f7f8fc; }}
    header {{ padding:28px; background:#191c25; border-bottom:1px solid #303545; }}
    main {{ max-width:1080px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 10px; font-size:28px; }}
    .summary,.context,.note {{ color:#bdc6df; line-height:1.45; }}
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
    code {{ color:#ffc857; }}
  </style>
</head>
<body>
  <header>
    <h1>Conversaciones Reddit traducidas a español latino</h1>
    <div class="summary">
      Texto visible traducido, corregido ortografica y gramaticalmente, preservando contexto. La DB guarda original y traduccion en <code>reddit_dialogue_text_candidates</code>.
    </div>
  </header>
  <main>{''.join(cards)}</main>
</body>
</html>
"""
    html_path.write_text(doc, encoding="utf-8")
    return {"html": str(html_path), "json": str(json_path), "csv": str(csv_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(latest_source()))
    args = parser.parse_args()
    source_path = Path(args.source)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    keys = load_keys()
    items = translate_items(source, keys)
    save_db(items)
    paths = write_html(items, source_path)
    print(json.dumps({"count": len(items), "paths": paths}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
