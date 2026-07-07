import html
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
ASSET_DIR = ROOT / "docs" / "prueba_assets"
OUT_PATH = ROOT / "docs" / "prueba.html"
CACHE_PATH = ROOT / "scratch" / "prueba_translation_cache.json"

SELECTED_IDS = [1, 17, 9, 2, 5, 8, 14, 152, 174, 181]
PROFILE_LABELS = {
    1: "coqueta",
    17: "indecisa",
    9: "defensiva",
    2: "desinteresada",
    5: "alta_selectividad (DB: stripper/sugar)",
    8: "indecisa",
    14: "defensiva",
    152: "coqueta",
    174: "desinteresada",
    181: "indecisa",
}
OCR_NOTES = {
    1: "OCR completo y legible para una sola imagen.",
    17: "OCR completo y legible para una sola imagen.",
    9: "OCR completo y legible para una sola imagen.",
    2: "OCR completo y legible para una sola imagen.",
    5: "OCR completo y legible para una sola imagen.",
    8: "Carrusel con OCR útil; algunos tiempos aparecen y se conservan solo cuando están en la data.",
    14: "Carrusel con OCR útil; no trae tiempos concretos en la estructura revisada.",
    152: "Carrusel con texto recuperado en transcription_json, pero transcription_text es demasiado corto.",
    174: "Carrusel con texto recuperado en transcription_json, pero transcription_text es demasiado corto.",
    181: "Carrusel con texto recuperado en transcription_json, pero transcription_text es demasiado corto.",
}

MANUAL_TRANSLATIONS = {
    "Girl|I love this ! This is such a match ✨": ("Ella", "Me encanta esto. Es una conexión total ✨"),
    "Me|Japan is amazing. We should go": ("Yo", "Japón es increíble. Deberíamos ir."),
    "Girl|We should !": ("Ella", "¡Deberíamos!"),
    "Me|We got some serious plans let me say": ("Yo", "Tenemos unos planes bastante serios, déjame decirte."),
    "Girl|Indeed. I love it": ("Ella", "Total. Me encanta."),
    "Girl|So what is your occupation, and your interests, hobby's, what do you dislike. I wanna know everything": (
        "Ella",
        "Entonces, ¿a qué te dedicas, cuáles son tus intereses, hobbies y qué no te gusta? Quiero saberlo todo.",
    ),
    "Me|I love food. My favourite colour is blue. Love soccer, pingpong and hanging out with friends. Being with family is for me important as well": (
        "Yo",
        "Me encanta la comida. Mi color favorito es el azul. Me gusta el fútbol, el ping-pong y salir con amigos. La familia también es importante para mí.",
    ),
    "Girl|Thank you so much for even recognizing my energy. I love yours too, it's such a match 🧿. Well I had to tell you about your amazing photo, I usually don't start conversations. So thank you for replying lolll.": (
        "Ella",
        "Gracias por reconocer mi energía. La tuya también me encanta, es una conexión total 🧿. Tenía que decirte lo increíble que está tu foto; normalmente no inicio conversaciones. Así que gracias por responder jajaja.",
    ),
    "Girl|Also you look perfect 🤩. Just perfect. I love your smile, facial hair, the shape of your eyes and your skin and mouth lol": (
        "Ella",
        "Además te ves perfecto 🤩. Perfecto de verdad. Me encanta tu sonrisa, tu barba, la forma de tus ojos, tu piel y tu boca jajaja.",
    ),
    "Emily|Depending what company lol": ("Emily", "Depende de qué compañía jajaja."),
    "Me|I get you, I get you haha. We should finally hit a workout sometime this week by the way! We can grab food after whatever, romantic little gym date?": (
        "Yo",
        "Te entiendo, te entiendo jaja. Por cierto, deberíamos entrenar por fin algún día de esta semana. Después podemos comer algo o lo que sea, ¿cita romántica de gimnasio?",
    ),
    "Emily|Ahaha we'll see": ("Emily", "Jajaja, ya veremos."),
    "Me|Hey Emily, I like you, but I need a yes or a no. If you dont want to meet in person, thats fine, you can feel free to tell me now and we can end this.": (
        "Yo",
        "Oye Emily, me gustas, pero necesito un sí o un no. Si no quieres vernos en persona, está bien; puedes decírmelo ahora y dejamos esto aquí.",
    ),
    "Me|If you just like to take more time before you meet someone, I understand and you can tell me, too, or whatever else. I don't want to waste any of our times, hope you can respect that.": (
        "Yo",
        "Si simplemente prefieres tomarte más tiempo antes de conocer a alguien, lo entiendo y también me lo puedes decir. No quiero hacerte perder el tiempo ni perder el mío; espero que puedas respetarlo.",
    ),
    "Emily|Damn it depends tbh but like I always take time to know the person before meeting and it depends on my schedule if I can meet lol 😂": (
        "Emily",
        "La verdad depende, pero yo siempre me tomo tiempo para conocer a la persona antes de verla, y también depende de mi horario si puedo quedar jajaja 😂",
    ),
    "Me|Alright cool, thanks for letting me know I understand. I do hate getting to know people over text, though, so how about we get on a Zoom call some time this week and hang out and chat?": (
        "Yo",
        "Bueno, perfecto, gracias por decírmelo, lo entiendo. Eso sí, odio conocer gente por texto; ¿qué tal si hacemos una llamada por Zoom esta semana, pasamos el rato y hablamos?",
    ),
    "Emily|Lol why over text 😂 idk if I have time for it since I work like everyday 😬": (
        "Emily",
        "Jaja, ¿por qué por texto? 😂 No sé si tenga tiempo para eso porque trabajo casi todos los días 😬",
    ),
    "Me|If you can't make time for a 30 minute zoom call nothing will ever come of this and we should just stop talking now.": (
        "Yo",
        "Si no puedes sacar tiempo para una llamada de Zoom de 30 minutos, esto no va a llegar a nada y mejor dejamos de hablar ahora.",
    ),
    "Guy|Are you a porn star": ("Hombre", "¿Eres actriz porno?"),
    "Me|No I'm unemployed": ("Yo", "No, estoy desempleada."),
    "Guy|😂 how's you're morning going": ("Hombre", "😂 ¿Cómo va tu mañana?"),
    "Guy|I heard U like starbuks": ("Hombre", "Escuché que te gusta Starbucks."),
    "Me|How did you hear that": ("Yo", "¿Cómo escuchaste eso?"),
    "Guy|I didnt . He lol jus said that so u can msg me": (
        "Hombre",
        "No lo escuché. Jaja, solo dije eso para que me escribieras.",
    ),
    "Guy|I'm not a simp though": ("Hombre", "Aunque no soy un simp."),
    "Guy|Ur dog looks lame": ("Hombre", "Tu perro se ve aburrido."),
    "Guy|Let me blow your back out": ("Hombre", "Déjame darte durísimo."),
    "Me|This why I don't usually swipe on guys holding fish": (
        "Yo",
        "Por esto normalmente no le doy swipe a tipos que salen sosteniendo peces.",
    ),
}


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def cache_translation(cache, row_id, source):
    suffix = f":{hash(source or '')}"
    for key, value in cache.items():
        if key.startswith(f"{row_id}:"):
            return value
    return None


def parse_json(value):
    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError:
        return []


def safe_asset(row_id, index, url):
    ASSET_DIR.mkdir(exist_ok=True)
    ext = Path(url.split("?")[0]).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    path = ASSET_DIR / f"case_{row_id}_{index}{ext}"
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=12) as response:
            path.write_bytes(response.read())
        return path
    except Exception:
        return None


def render_messages(messages):
    parts = []
    for msg in messages:
        if "autor" in msg:
            speaker = msg.get("autor") or "N/A"
            text = msg.get("texto") or ""
            time_value = msg.get("tiempo")
        else:
            key = f"{msg.get('sender')}|{msg.get('text')}"
            speaker, text = MANUAL_TRANSLATIONS.get(key, (msg.get("sender") or "N/A", msg.get("text") or ""))
            time_value = msg.get("time")
        time_html = ""
        if time_value and str(time_value).strip().upper() not in {"N/A", "NA", "NONE"}:
            time_html = f'<span class="time">{html.escape(str(time_value))}</span>'
        parts.append(
            f'<div class="msg"><strong>{html.escape(str(speaker))}</strong>{time_html}'
            f'<p>{html.escape(str(text))}</p></div>'
        )
    return "\n".join(parts)


def markdownish_to_html(text):
    lines = [line.strip() for line in (text or "").splitlines()]
    chunks = []
    for line in lines:
        if not line:
            continue
        line = html.escape(line)
        line = line.replace("**", "")
        chunks.append(f"<p>{line}</p>")
    return "\n".join(chunks)


def case_translation(cache, row):
    source = row["transcription_text"] or ""
    cached = cache_translation(cache, row["id"], source)
    if cached:
        return markdownish_to_html(cached)
    data = parse_json(row["transcription_json"])
    if isinstance(data, dict) and isinstance(data.get("mensajes"), list):
        return render_messages(data["mensajes"])
    if isinstance(data, list):
        return render_messages(data)
    return markdownish_to_html(source)


def db_counts(con):
    rows = []
    for post_type, total, with_json, with_text in con.execute(
        """
        select post_type,
               count(*),
               sum(case when transcription_json is not null and transcription_json != '' then 1 else 0 end),
               sum(case when transcription_text is not null and transcription_text != '' then 1 else 0 end)
        from reddit_conversations
        group by post_type
        order by post_type
        """
    ):
        rows.append((post_type, total, with_json, with_text))
    profiles = []
    for profile, post_type, total, with_json in con.execute(
        """
        select coalesce(girl_profile_type, 'NULL'), post_type, count(*),
               sum(case when transcription_json is not null and transcription_json != '' then 1 else 0 end)
        from reddit_conversations
        group by coalesce(girl_profile_type, 'NULL'), post_type
        order by 1, 2
        """
    ):
        profiles.append((profile, post_type, total, with_json))
    return rows, profiles


def render_image_block(row_id, urls):
    images = []
    for index, url in enumerate(urls, start=1):
        asset = safe_asset(row_id, index, url)
        src = asset.relative_to(OUT_PATH.parent).as_posix() if asset else url
        images.append(
            f'<figure><img src="{html.escape(src)}" alt="Imagen original {row_id}-{index}">'
            f'<figcaption>Imagen {index}</figcaption></figure>'
        )
    cls = "media carousel" if len(images) > 1 else "media"
    return f'<div class="{cls}">' + "\n".join(images) + "</div>"


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cache = load_cache()
    rows = [
        con.execute("select * from reddit_conversations where id = ?", (row_id,)).fetchone()
        for row_id in SELECTED_IDS
    ]
    rows = [row for row in rows if row]
    counts, profiles = db_counts(con)
    transcript_status = list(con.execute("select status, count(*) from transcripts group by status order by status"))
    reddit_cases = len(list((ROOT / "reddit_cases").glob("*.json"))) if (ROOT / "reddit_cases").exists() else 0
    parsed_cases = len(list((ROOT / "parsed_cases").glob("*.json"))) if (ROOT / "parsed_cases").exists() else 0
    failed_cases = len(list((ROOT / "failed_cases").glob("*.json"))) if (ROOT / "failed_cases").exists() else 0

    case_cards = []
    for row in rows:
        urls = parse_json(row["image_urls"])
        original_ocr = row["transcription_text"] or ""
        card = f"""
        <article class="case-card">
          <header>
            <div>
              <p class="kicker">ID DB {row['id']} · Post {html.escape(row['post_id'] or '')}</p>
              <h2>{html.escape(row['title'] or 'Sin titulo')}</h2>
            </div>
            <div class="badges">
              <span>{html.escape(row['post_type'] or '')}</span>
              <span>{html.escape(PROFILE_LABELS.get(row['id'], row['girl_profile_type'] or 'sin perfil'))}</span>
            </div>
          </header>
          <div class="case-grid">
            {render_image_block(row['id'], urls)}
            <section class="conversation">
              <h3>Conversacion traducida</h3>
              {case_translation(cache, row)}
              <p class="note">{html.escape(OCR_NOTES.get(row['id'], 'Revisado desde DB.'))}</p>
              <details>
                <summary>Ver transcripcion OCR original guardada en DB</summary>
                <pre>{html.escape(original_ocr)}</pre>
              </details>
            </section>
          </div>
        </article>
        """
        case_cards.append(card)

    html_doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prueba OCR Reddit - Easy Date</title>
  <style>
    :root {{
      --bg: #f6f5f2;
      --ink: #202124;
      --muted: #69635d;
      --line: #d8d2ca;
      --panel: #ffffff;
      --accent: #256f6c;
      --accent-2: #8c3d3d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      line-height: 1.5;
    }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }}
    h1 {{ font-size: 32px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 20px; margin: 4px 0 0; letter-spacing: 0; }}
    h3 {{ margin: 0 0 12px; font-size: 16px; letter-spacing: 0; }}
    p {{ margin: 0 0 10px; }}
    .intro {{ color: var(--muted); max-width: 900px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 24px 0; }}
    .panel, .case-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }}
    .panel {{ padding: 18px; overflow: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 700; }}
    .case-card {{ margin: 18px 0; padding: 18px; }}
    .case-card > header {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }}
    .kicker {{ color: var(--muted); font-size: 13px; margin: 0; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .badges span {{ border: 1px solid var(--line); color: var(--accent); padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
    .case-grid {{ display: grid; grid-template-columns: minmax(280px, 46%) minmax(0, 1fr); gap: 18px; align-items: start; }}
    .media {{ display: grid; gap: 10px; }}
    .media.carousel {{ display: flex; overflow-x: auto; scroll-snap-type: x proximity; padding-bottom: 10px; }}
    figure {{ margin: 0; min-width: 100%; scroll-snap-align: start; }}
    .carousel figure {{ min-width: min(86%, 460px); }}
    img {{ width: 100%; height: auto; max-height: 720px; object-fit: contain; border: 1px solid var(--line); border-radius: 6px; background: #eee; display: block; }}
    figcaption {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .conversation {{ border-left: 3px solid var(--accent); padding-left: 16px; }}
    .conversation p {{ white-space: pre-wrap; }}
    .msg {{ border-bottom: 1px solid var(--line); padding: 9px 0; }}
    .msg strong {{ color: var(--accent-2); margin-right: 8px; }}
    .msg p {{ margin: 4px 0 0; }}
    .time {{ color: var(--muted); font-size: 12px; }}
    .note {{ margin-top: 12px; color: var(--accent-2); font-weight: 700; }}
    details {{ margin-top: 12px; }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 700; }}
    pre {{ white-space: pre-wrap; background: #f0ede7; border: 1px solid var(--line); border-radius: 6px; padding: 12px; overflow: auto; }}
    @media (max-width: 820px) {{
      main {{ width: min(100% - 20px, 1180px); }}
      .summary-grid, .case-grid {{ grid-template-columns: 1fr; }}
      .case-card > header {{ display: block; }}
      .badges {{ justify-content: flex-start; margin-top: 10px; }}
      .conversation {{ border-left: 0; border-top: 3px solid var(--accent); padding: 14px 0 0; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Prueba OCR Reddit - Easy Date</h1>
  <p class="intro">Muestra generada desde <strong>textgame.db</strong>. No se agregaron mensajes ni tiempos fuera de la data: los tiempos solo aparecen cuando estaban en la estructura OCR/transcription_json. Como la carpeta original <strong>downloaded_files</strong> no esta presente, este HTML usa copias redescargadas en <strong>prueba_assets</strong> y conserva las URL originales de Reddit como respaldo.</p>

  <section class="summary-grid">
    <div class="panel">
      <h3>Reddit por tipo</h3>
      <table><thead><tr><th>Tipo</th><th>Total</th><th>Con JSON OCR</th><th>Con texto OCR</th></tr></thead><tbody>
        {''.join(f'<tr><td>{html.escape(str(a))}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a,b,c,d in counts)}
      </tbody></table>
    </div>
    <div class="panel">
      <h3>Perfiles Reddit</h3>
      <table><thead><tr><th>Perfil DB</th><th>Tipo</th><th>Total</th><th>Con OCR</th></tr></thead><tbody>
        {''.join(f'<tr><td>{html.escape(str(a))}</td><td>{html.escape(str(b))}</td><td>{c}</td><td>{d}</td></tr>' for a,b,c,d in profiles)}
      </tbody></table>
    </div>
    <div class="panel">
      <h3>YouTube y primer escaneo</h3>
      <table><tbody>
        {''.join(f'<tr><td>transcripts: {html.escape(str(a))}</td><td>{b}</td></tr>' for a,b in transcript_status)}
        <tr><td>reddit_cases/*.json</td><td>{reddit_cases}</td></tr>
        <tr><td>parsed_cases/*.json</td><td>{parsed_cases}</td></tr>
        <tr><td>failed_cases/*.json</td><td>{failed_cases}</td></tr>
      </tbody></table>
    </div>
    <div class="panel">
      <h3>Notas de cobertura</h3>
      <p>No existe el perfil literal <strong>alta_selectividad</strong> en la columna <strong>girl_profile_type</strong>. Para la muestra single_image se uso <strong>stripper/sugar</strong> como equivalente operativo de alta selectividad. En carrusel no hay casos alta_selectividad/stripper/sugar/MILF, por eso los 5 carruseles cubren los perfiles disponibles.</p>
    </div>
  </section>

  {''.join(case_cards)}

  <p class="intro">Generado el {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} desde SQLite local.</p>
</main>
</body>
</html>
"""
    OUT_PATH.write_text(html_doc, encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
