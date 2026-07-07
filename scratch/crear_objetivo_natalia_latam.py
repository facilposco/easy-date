import csv
import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"
RAW_DIR = ROOT / "scratch" / "reddit_objective_dialogue_scan_raw"

SELECTED = [
    "elz690",
    "pvy9zp",
    "b2ja2r",
    "akzf6b",
    "jtx9m4",
    "bpdnhs",
    "dofa36",
    "pj2b3q",
    "bcb2q8",
    "dsa1xy",
]

LATAM = {
    "elz690": {
        "objective": "cita",
        "title_es": "Logró recuperarse y consiguió una cita para el fin de semana",
        "note": "Apto con cautela: logra cita, pero el último mensaje es sexual y debe usarse como ejemplo de riesgo/calibración.",
        "turns": [
            "Bueno, estás guapo.",
            "Debes estar viendo tu reflejo en la pantalla del celular.",
            "Ohh, suave.",
            "¿Cuáles son las tres cosas favoritas que buscas en un hombre?",
            "Mmm... alguien con metas y la cabeza bien puesta, que sepa tratar a la gente, que sea amable y respetuoso, que tenga buen corazón y que me haga reír.",
            "Bueno, eso fueron seis cosas, pero por suerte no estoy aquí buscando a alguien buena en matemáticas.",
            "Y si no puedes distinguir entre tres y seis, entonces mi pene es perfecto para ti.",
        ],
    },
    "pvy9zp": {
        "objective": "cita",
        "title_es": "La cita quedó acordada, pero ella pidió una nota de voz para sentirse segura",
        "note": "Apto: muestra cierre de cita y manejo de una objeción de seguridad.",
        "turns": [
            "Solo mándame un audio diciendo que no me vas a secuestrar ni matar.",
            "También podríamos vernos un poco más tarde si quieres comer algo con tus compañeros después del trabajo.",
            "Jaja, no te preocupes.",
            "¿Qué? Jajaja.",
            "Bueno, entonces queda listo. Nos vemos el martes.",
            "¿Estás bien con mi pequeña petición?",
            "¿Lo dices en broma, verdad?",
            "Puede parecerte raro, pero de verdad me sentiría mejor si lo recibo.",
        ],
    },
    "b2ja2r": {
        "objective": "telefono",
        "title_es": "Juego de rol en Tinder que termina con intercambio de número",
        "note": "Apto: ejemplo claro de dinámica lúdica que lleva a contacto.",
        "turns": [
            "Elige tu propia aventura... E. Explorar la cueva buscando pistas.",
            "Normalmente elegiría B... pero hoy me siento bien y con suerte, así que E.",
            "[El juego de rol continúa hasta que él da su número como si fuera un código].",
            "[Número]!!!!!!!!",
        ],
    },
    "akzf6b": {
        "objective": "telefono",
        "title_es": "Consiguió su primer número después de una apertura creativa",
        "note": "Apto: buen ejemplo de humor ligero y respuesta femenina receptiva.",
        "turns": [
            "¿Cuál es tu bebida favorita? ¿Licor fuerte, cerveza o la sangre de tus víctimas?",
            "Cosmo.",
            "Ahhh, una viajera del tiempo... Hagamos un viaje a los 80.",
            "[Imagen de un DeLorean].",
            "Me caes bien.",
            "Escríbeme.",
        ],
    },
    "jtx9m4": {
        "objective": "telefono",
        "title_es": "El número más rápido que consiguió",
        "note": "Apto: excelente ejemplo de identidad juguetona y cierre natural a intercambio de contactos.",
        "turns": [
            "PAPÁ DE PLANTAS.",
            "¿Me llamabas? También me gusta el término padre del follaje.",
            "¿Puedo ponerte así como nombre de contacto?",
            "Claro, suena mucho mejor que [nombre]. ¿Intercambiamos contactos ya?",
            "Sí, eso haremos.",
            "[Comparte número de teléfono].",
            "Ponme a mí como perra botánica.",
        ],
    },
    "bpdnhs": {
        "objective": "telefono/cita",
        "title_es": "Consiguió el número después de un abridor oscuro",
        "note": "Apto con cautela: funciona por complicidad, pero el tema oscuro puede ser riesgoso según perfil.",
        "turns": [
            "Gracias, gracias.",
            "Ahora vayamos al grano. ¿Cuál es el mejor lugar para esconder un cuerpo?",
            "No, no, no. Uno asesina y esconde al mismo tiempo: vas de excursión y los empujas por un acantilado o una montaña.",
            "Ohhh, ya veo lo que dices.",
            "Siguiente tema: ideas para una cita :)",
            "Estaba pensando que podríamos ir de excursión.",
            "Maravillosa idea. Veamos quién vuelve.",
            "Wow, creo que me acabo de enamorar.",
        ],
    },
    "dofa36": {
        "objective": "telefono",
        "title_es": "Un juego de palabras cursi que terminó en número",
        "note": "Apto: muestra cómo un chiste simple puede funcionar si ella entra en el juego.",
        "turns": [
            "Oye, creo que tú y yo tenemos un amigo en común.",
            "¡Hola! ¿Cómo se llama?",
            "Joe.",
            "¿Joe quién?",
            "¿Me das jo-e número?",
            "Mi intolerancia a la lactosa está molesta por lo cursi que fue eso, pero personalmente me encantó.",
        ],
    },
    "pj2b3q": {
        "objective": "telefono/cita",
        "title_es": "Consiguió una cena y el teléfono",
        "note": "Apto: ejemplo claro de avance suave hacia cita + número.",
        "turns": [
            "Las rosas son rojas, las violetas azules, ¿cómo tuve tanta suerte de hacer match contigo? Las margaritas son blancas, los tulipanes rosados, quizá algún día podría invitarte algo de tomar.",
            "Eres muy dulce, me encantaría. Solo tengo que decirte que tendría que ser una soda porque tristemente no puedo entrar a un bar.",
            "Ah, cierto, se me olvidó que todavía eres muy joven. Una soda funciona. Creo que la soda también combina bien con una cena.",
            "¿Entonces ahora también es cena?",
            "Parece lo natural. Sería raro ir a algún lugar y comprarte solo una soda.",
            "Me parece justo. Me encantaría ir a cenar contigo.",
            "Teléfono: [número].",
        ],
    },
    "bcb2q8": {
        "objective": "telefono",
        "title_es": "Usó a su perro para conseguir el número",
        "note": "Apto: cierre creativo, indirecto y de baja presión.",
        "turns": [
            "Tu perro era demasiado lindo como para no darte like.",
            "Le preguntaré a mi perra si quiere mantenerse en contacto.",
            "Dios mío, jajaja.",
            "Dijo que sí.",
            "Pero pidió tu número porque obviamente no usa Tinder...",
            "Digo, es una perra... ¿qué esperabas?",
            "Está bien, aceptaré.",
            "[Número de teléfono].",
        ],
    },
    "dsa1xy": {
        "objective": "cita",
        "title_es": "La conversación formal que terminó en acuerdo para salir",
        "note": "Apto: ejemplo de juego de rol formal y avance directo a cita.",
        "turns": [
            "Yo saldría contigo.",
            "Yo también saldría contigo.",
            "Perfecto, salgamos. Informaré a mis unidades parentales para ver si tenemos su bendición. Te recomiendo hacer lo mismo. Gracias de antemano.",
            "De acuerdo. Aprecio tu tiempo y flexibilidad en este asunto. Por favor, notifícame cualquier cambio. Saludos.",
            "Brenna, agradezco tu rápida respuesta. Acabo de conversar con mi madre y dijo que es aceptable, con leve emoción. Quedo atento a tu respuesta.",
        ],
    },
}


def normalize_sender(sender):
    s = (sender or "").lower()
    if s in {"me", "him", "guy", "man", "jon", "benjamin", "josh"}:
        return "hombre"
    if s in {"girl", "her", "woman", "erin", "maddy", "brenna", "mary"}:
        return "mujer"
    return "hombre" if s == "me" else "mujer"


def ensure_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reddit_objective_dialogue_candidates (
            post_id TEXT PRIMARY KEY,
            source_url TEXT,
            title_original TEXT,
            title_es TEXT,
            profile_type TEXT,
            objective TEXT,
            messages_original_json TEXT,
            messages_es_json TEXT,
            quality_score INTEGER,
            quality_note_es TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )


def load_items():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        items = []
        for post_id in SELECTED:
            row = conn.execute(
                """
                SELECT post_id,title,url,score,girl_profile_type,transcription_json
                FROM reddit_conversations
                WHERE post_id=?
                """,
                (post_id,),
            ).fetchone()
            if not row:
                continue
            original = json.loads(row["transcription_json"])
            tr = LATAM[post_id]
            messages_es = []
            for original_msg, text_es in zip(original, tr["turns"]):
                messages_es.append(
                    {
                        "speaker": normalize_sender(original_msg.get("sender")),
                        "sender_original": original_msg.get("sender"),
                        "text_es": text_es,
                    }
                )
            items.append({"row": dict(row), "original": original, "translation": tr, "messages_es": messages_es})
        return items
    finally:
        conn.close()


def save_db(items):
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
        now = datetime.now().isoformat(timespec="seconds")
        for item in items:
            row = item["row"]
            tr = item["translation"]
            conn.execute(
                """
                INSERT INTO reddit_objective_dialogue_candidates (
                    post_id, source_url, title_original, title_es, profile_type,
                    objective, messages_original_json, messages_es_json,
                    quality_score, quality_note_es, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    source_url=excluded.source_url,
                    title_original=excluded.title_original,
                    title_es=excluded.title_es,
                    profile_type=excluded.profile_type,
                    objective=excluded.objective,
                    messages_original_json=excluded.messages_original_json,
                    messages_es_json=excluded.messages_es_json,
                    quality_score=excluded.quality_score,
                    quality_note_es=excluded.quality_note_es,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (
                    row["post_id"],
                    row["url"],
                    row["title"],
                    tr["title_es"],
                    row["girl_profile_type"],
                    tr["objective"],
                    json.dumps(item["original"], ensure_ascii=False),
                    json.dumps(item["messages_es"], ensure_ascii=False),
                    row["score"],
                    tr["note"],
                    "objetivo_validado_latam",
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def write_outputs(items):
    DOCS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = DOCS_DIR / f"reddit_objetivo_natalia_latam_{stamp}.html"
    csv_path = DOCS_DIR / f"reddit_objetivo_natalia_latam_{stamp}.csv"
    json_path = RAW_DIR / f"reddit_objetivo_natalia_latam_{stamp}.json"

    payload = []
    for item in items:
        row = item["row"]
        tr = item["translation"]
        payload.append(
            {
                "post_id": row["post_id"],
                "source_url": row["url"],
                "title_original": row["title"],
                "title_es": tr["title_es"],
                "profile_type": row["girl_profile_type"],
                "objective": tr["objective"],
                "quality_score": row["score"],
                "quality_note_es": tr["note"],
                "messages_original": item["original"],
                "messages_es": item["messages_es"],
            }
        )
    json_path.write_text(json.dumps({"results": payload}, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "post_id", "objective", "profile_type", "quality_score", "title_es", "status"])
        for rank, item in enumerate(payload, 1):
            writer.writerow([rank, item["post_id"], item["objective"], item["profile_type"], item["quality_score"], item["title_es"], "objetivo_validado_latam"])

    cards = []
    for rank, item in enumerate(payload, 1):
        turns_html = "".join(
            f"<div class='turn {msg['speaker']}'><b>{'Hombre' if msg['speaker'] == 'hombre' else 'Mujer'}</b><p>{html.escape(msg['text_es'])}</p></div>"
            for msg in item["messages_es"]
        )
        cards.append(
            f"""
            <article class="case">
              <div class="rank">#{rank}</div>
              <div class="meta">
                <span>Objetivo: {html.escape(item['objective'])}</span>
                <span>Perfil: {html.escape(str(item['profile_type']))}</span>
                <span>Score Reddit: {item['quality_score']}</span>
                <span>DB: objetivo validado</span>
              </div>
              <h2>{html.escape(item['title_es'])}</h2>
              <a href="{html.escape(item['source_url'])}" target="_blank" rel="noreferrer">Abrir fuente original</a>
              <p class="note">{html.escape(item['quality_note_es'])}</p>
              <section class="dialogue">{turns_html}</section>
              <details><summary>Original OCR</summary><pre>{html.escape(json.dumps(item['messages_original'], ensure_ascii=False, indent=2))}</pre></details>
            </article>
            """
        )

    doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Easy Date - 10 conversaciones con objetivo logrado</title>
  <style>
    body {{ margin:0; font-family: Arial, sans-serif; background:#101116; color:#f7f8fc; }}
    header {{ padding:28px; background:#191c25; border-bottom:1px solid #303545; }}
    main {{ max-width:1080px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 10px; font-size:28px; }}
    .summary,.note {{ color:#bdc6df; line-height:1.45; }}
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
    pre {{ white-space:pre-wrap; overflow:auto; background:#11141d; padding:12px; border-radius:8px; }}
  </style>
</head>
<body>
  <header>
    <h1>10 conversaciones con objetivo logrado</h1>
    <div class="summary">
      Casos tomados de <code>textgame.db</code>, traducidos y corregidos a español latino. Objetivo válido: teléfono/número, contacto o cita acordada.
    </div>
  </header>
  <main>{''.join(cards)}</main>
</body>
</html>
"""
    html_path.write_text(doc, encoding="utf-8")
    return {"html": str(html_path), "csv": str(csv_path), "json": str(json_path)}


def main():
    items = load_items()
    save_db(items)
    paths = write_outputs(items)
    print(json.dumps({"count": len(items), "paths": paths}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
