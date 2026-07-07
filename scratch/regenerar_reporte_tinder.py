import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


TIME_RE = re.compile(
    r"(?i)\b(?:today|yesterday)?\s*(?:[a-z]{3}\s*\d{1,2},?\s*\d{4},?\s*)?(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?\b"
)


NOISE_RE = re.compile(
    r"(?i)^(?:at&t|verizon|t-mobile|sprint|lte|5g|wi-?fi|messages?\(?\d*\)?|details|send|type a message|"
    r"escribe un mensaje|imessage|gif|pay|[a-z]?|[®©]|[0-9]{1,3}%|[0-9]{1,3}%\s+\d{1,2}:\d{2})$"
)


def parse_time(line):
    match = TIME_RE.search(line or "")
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = (match.group(3) or "").lower().replace(".", "")
    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    return hour * 60 + minute, match.group(0).strip()


def fmt_delta(minutes):
    if minutes is None:
        return ""
    if minutes < 0:
        return ""
    if minutes < 60:
        return f"{minutes} min"
    hours, mins = divmod(minutes, 60)
    return f"{hours} h {mins} min" if mins else f"{hours} h"


def clean_lines(text):
    lines = []
    for raw in (text or "").splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        if NOISE_RE.match(line):
            continue
        lines.append(line)
    return lines


def build_messages(row):
    ocr_lines = clean_lines(row.get("ocr_text", ""))
    translated = clean_lines(row.get("translation_es", ""))
    source_lines = translated or ocr_lines
    if not source_lines:
        return [], []

    timeline = []
    last_time = None
    for idx, line in enumerate(ocr_lines):
        parsed = parse_time(line)
        if not parsed:
            continue
        minutes, label = parsed
        # Ignore first status-bar time unless another message timestamp appears later.
        timeline.append({"line": idx, "minutes": minutes, "label": label, "delta": None})
        if last_time is not None:
            timeline[-1]["delta"] = fmt_delta(minutes - last_time)
        last_time = minutes
    if len(timeline) < 2:
        timeline = []

    messages = []
    current = []
    for line in source_lines:
        if parse_time(line):
            continue
        current.append(line)
        ends = re.search(r"[.!?¡¿:]$|jaja|haha|lol", line, re.I)
        if len(current) >= 2 or ends:
            messages.append(" ".join(current))
            current = []
    if current:
        messages.append(" ".join(current))

    compact = []
    for msg in messages:
        msg = re.sub(r"\s+", " ", msg).strip()
        if len(msg) < 2 or NOISE_RE.match(msg):
            continue
        compact.append(msg)
    return compact[:24], timeline


def render_report(input_json, output_html):
    data = json.loads(Path(input_json).read_text(encoding="utf-8"))
    rows = sorted(data["results"], key=lambda row: (-int(row.get("score", 0)), row.get("category", ""), row.get("title_es", "")))

    cards = []
    categories = sorted({r.get("category", "sin_categoria") for r in rows})
    options = "".join(f"<option value='{html.escape(c)}'>{html.escape(c.replace('_', ' '))}</option>" for c in categories)

    for idx, row in enumerate(rows, 1):
        messages, timeline = build_messages(row)
        bubbles = []
        for mi, msg in enumerate(messages):
            side = "me" if mi % 2 == 0 else "her"
            who = "El" if side == "me" else "Ella"
            timing = ""
            if mi < len(timeline):
                label = timeline[mi]["label"]
                delta = timeline[mi].get("delta")
                timing = f"<span class='time-chip'>Hora: {html.escape(label)}" + (f" · Demora: {html.escape(delta)}" if delta else "") + "</span>"
            bubbles.append(
                f"<div class='msg {side}'><div class='speaker'>{who}</div><div class='bubble'>{html.escape(msg)}</div>{timing}</div>"
            )
        if not bubbles:
            bubbles.append("<div class='empty-note'>No hay conversacion traducida suficiente para renderizar burbujas.</div>")

        time_note = (
            "<p class='time-note ok'>Tiempos detectados desde la captura. Las demoras se calculan solo entre marcas OCR consecutivas.</p>"
            if timeline
            else "<p class='time-note'>Sin demora calculable: la captura no trae marcas de hora suficientes o solo muestra la hora de la barra del telefono.</p>"
        )
        images = "".join(
            f"<a href='{html.escape(Path(path).as_posix())}' target='_blank' rel='noreferrer'><img src='{html.escape(Path(path).as_posix())}' alt='captura original'></a>"
            for path in row.get("local_paths", [])
        )
        objectives = ", ".join(row.get("objectives", [])) or "conexion/humor"
        category = row.get("category", "sin_categoria")
        search = html.escape(" ".join([row.get("title_es", ""), row.get("title", ""), row.get("translation_es", ""), objectives]).lower())
        cards.append(
            f"""
            <article class="case" data-score="{row.get('score', 0)}" data-category="{html.escape(category)}" data-search="{search}">
              <div class="case-top">
                <div>
                  <p class="eyebrow">#{idx} · {html.escape(category.replace('_', ' '))}</p>
                  <h2>{html.escape(row.get('title_es') or row.get('title') or 'Caso Reddit')}</h2>
                </div>
                <strong class="score">Scoring: {row.get('score', 0)}/10</strong>
              </div>
              <div class="meta"><span>{html.escape(objectives)}</span><span>{html.escape(row.get('subreddit', ''))}</span><a href="{html.escape(row.get('source_url', ''))}" target="_blank" rel="noreferrer">Post original</a></div>
              <p class="summary">{html.escape(row.get('summary_es', ''))}</p>
              {time_note}
              <div class="split">
                <aside class="original">
                  <h3>Imagen original</h3>
                  <div class="imgs">{images}</div>
                </aside>
                <section class="phone">
                  <div class="phone-head">
                    <span class="back">‹</span>
                    <span class="avatar">N</span>
                    <span>Conversacion traducida</span>
                    <span class="dots">•••</span>
                  </div>
                  <div class="chat">{''.join(bubbles)}</div>
                </section>
              </div>
            </article>
            """
        )

    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Easy Date · Casos Reddit Tinder</title>
<style>
:root{{color-scheme:dark;--bg:#101114;--panel:#171b23;--phone:#05070b;--line:#323743;--text:#f8fafc;--muted:#9ca3af;--pink:#c91863;--blue:#2a57de;--green:#20d493}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#1d2330 0,#101114 45%);color:var(--text);font-family:Inter,Arial,sans-serif}}header,main{{max-width:1320px;margin:auto;padding:18px}}h1{{margin:0 0 6px;font-size:28px}}.toolbar{{position:sticky;top:0;z-index:10;background:rgba(16,17,20,.94);border-block:1px solid var(--line);padding:10px 18px;backdrop-filter:blur(12px)}}.toolbar-inner{{max-width:1320px;margin:auto;display:grid;grid-template-columns:1fr 230px 170px;gap:10px}}input,select{{background:#242936;color:var(--text);border:1px solid var(--line);border-radius:999px;padding:10px 14px;font-size:14px}}.case{{background:var(--panel);border:1px solid var(--line);border-radius:8px;margin:16px 0;overflow:hidden;box-shadow:0 20px 70px rgba(0,0,0,.28)}}.case-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;padding:18px 20px;border-bottom:1px solid var(--line)}}.eyebrow{{margin:0 0 5px;color:var(--muted);text-transform:uppercase;font-size:11px;letter-spacing:.08em}}h2{{margin:0;font-size:23px;line-height:1.2}}.score{{background:#20375d;color:#5da0ff;border-radius:999px;padding:8px 12px;font-size:18px;white-space:nowrap}}.meta{{display:flex;gap:8px;flex-wrap:wrap;padding:12px 20px 0}}.meta span,.meta a{{background:#252d3b;color:#dbeafe;border-radius:999px;padding:6px 9px;text-decoration:none;font-size:13px}}.summary,.time-note{{padding:0 20px;color:#d7dce8;font-size:14px}}.time-note{{color:#ffca6a}}.time-note.ok{{color:#8ee6ba}}.split{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0;border-top:1px solid var(--line)}}.phone{{background:var(--phone);min-height:420px;border-left:1px solid var(--line);min-width:0}}.phone-head{{height:42px;display:flex;align-items:center;gap:8px;padding:0 12px;border-bottom:1px solid rgba(255,255,255,.08);font-size:14px;font-weight:700}}.back{{font-size:25px;color:#d3d3d3}}.avatar{{width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#ff4d86,#8b5cf6);display:grid;place-items:center;font-size:14px}}.dots{{margin-left:auto;color:#c7c7c7}}.chat{{padding:17px 15px 20px;display:flex;flex-direction:column;gap:10px;width:100%;max-width:720px;margin:0 auto}}.msg{{width:fit-content;max-width:min(68%,430px);display:flex;flex-direction:column;gap:3px}}.msg.me{{align-self:flex-start;margin-left:20%;align-items:flex-start}}.msg.her{{align-self:flex-start;margin-left:8%;align-items:flex-start}}.speaker{{font-size:10px;color:#aaa}}.bubble{{padding:10px 13px;border-radius:15px;font-size:13px;line-height:1.28;white-space:pre-wrap;overflow-wrap:anywhere;color:#fff}}.me .bubble{{background:var(--blue);border-bottom-right-radius:4px}}.her .bubble{{background:var(--pink);border-bottom-left-radius:4px}}.time-chip{{font-size:10px;color:#b5becd;background:#2b303b;border-radius:999px;padding:3px 6px}}.original{{background:#07090d;padding:16px;min-width:0}}.original h3{{margin:0 0 10px;color:#cbd5e1;font-size:15px}}.imgs{{display:flex;gap:12px;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;padding-bottom:10px;justify-content:flex-start;max-width:100%;overscroll-behavior-x:contain}}.imgs a{{flex:0 0 100%;scroll-snap-align:start;display:flex;justify-content:center}}.imgs img{{width:auto;max-width:96%;max-height:760px;object-fit:contain;border-radius:8px;background:#fff}}.hidden{{display:none}}.empty-note{{color:#cbd5e1;background:#303642;padding:12px;border-radius:8px;font-size:13px}}#empty{{display:none;text-align:center;color:var(--muted);padding:28px}}
@media(max-width:900px){{.toolbar-inner{{grid-template-columns:1fr}}.case-top{{display:block}}.score{{display:inline-block;margin-top:10px}}.split{{grid-template-columns:1fr}}.phone{{border-left:0;border-top:1px solid var(--line)}}.msg{{max-width:72%}}.msg.me{{margin-left:18%}}.msg.her{{margin-left:6%}}.bubble{{font-size:13px}}.imgs a{{flex-basis:100%}}.imgs img{{max-width:96%}}}}
</style>
</head>
<body>
<header><h1>Easy Date · Casos reales Reddit</h1><p>Vista estilo Tinder. La transcripcion tecnica queda conservada en JSON/SQLite para auditoria y entrenamiento, pero no se muestra aqui.</p></header>
<div class="toolbar"><div class="toolbar-inner"><input id="q" type="search" placeholder="Buscar caso, objetivo o traduccion..."><select id="cat"><option value="">Todas las categorias</option>{options}</select><select id="minScore"><option value="0">Score minimo</option><option value="9">9+</option><option value="8">8+</option><option value="7">7+</option><option value="6">6+</option></select></div></div>
<main>{''.join(cards)}<div id="empty">No hay casos con esos filtros.</div></main>
<script>
function filterCases(){{
  const q=document.getElementById('q').value.trim().toLowerCase();
  const cat=document.getElementById('cat').value;
  const min=Number(document.getElementById('minScore').value||0);
  let visible=0;
  document.querySelectorAll('.case').forEach(card=>{{
    const show=(!q||card.dataset.search.includes(q))&&(!cat||card.dataset.category===cat)&&Number(card.dataset.score)>=min;
    card.classList.toggle('hidden',!show);
    if(show) visible++;
  }});
  document.getElementById('empty').style.display=visible?'none':'block';
}}
document.getElementById('q').addEventListener('input',filterCases);
document.getElementById('cat').addEventListener('change',filterCases);
document.getElementById('minScore').addEventListener('change',filterCases);
</script>
</body>
</html>"""
    Path(output_html).write_text(doc, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_html")
    args = parser.parse_args()
    render_report(args.input_json, args.output_html)


if __name__ == "__main__":
    main()
