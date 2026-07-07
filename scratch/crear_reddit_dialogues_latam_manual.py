import csv
import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scratch" / "reddit_dialogue_text_scan_raw" / "reddit_dialogues_text_top10_20260630_200826.json"
DB_PATH = ROOT / "textgame.db"
DOCS_DIR = ROOT / "docs"
RAW_DIR = ROOT / "scratch" / "reddit_dialogue_text_scan_raw"


TRANSLATIONS = {
    "u48ije": {
        "title_es": "Una match de Tinder me criticó por mi forma de conversar después de varios días hablando",
        "context_es": "Caso útil: conversación real con retroalimentación directa de la mujer sobre un abridor flojo.",
        "quality_note_es": "Apto para Natalia: buen ejemplo de cómo un comentario superficial puede bajar la atracción.",
        "turns": [
            "9:49 Hola.",
            "9:49 Tu espejo está algo sucio.",
            "10:42 Bueno... tienes unos ojos muy lindos...",
            "9:14 Ya llevas tiempo en este juego, [mi nombre].",
            "9:19 ¿Cuál juego?",
            "9:20 El juego de Tinder.",
            "9:20 Sí... pero ¿cómo lo supiste?",
            "9:23 Porque yo también.",
            "9:23 Ya me has escrito como dos veces antes.",
            "9:23 Dios nos ayude.",
            "9:23 Jaja.",
            "9:23 No lo recuerdo para nada.",
            "9:23 ¿Cuándo fue y qué dije?",
            "9:24 ¿Segura de que no era alguien que se parecía a mí?",
            "9:24 No sé. No, eras tú, jajaja, y probablemente fue mejor que comentar lo del espejo.",
            "9:25 De verdad creo que te recordaría... ¿sí conversamos o mi primer mensaje no funcionó?",
        ],
    },
    "4wraan": {
        "title_es": "De fracasar a mejorar pidiendo números: reporte de campo de un principiante",
        "context_es": "Caso de transición a WhatsApp/número. Tiene respuesta femenina clara y límite: ella tiene novio.",
        "quality_note_es": "Uso secundario: sirve para analizar límites y calibración; no es un ejemplo ideal de cierre.",
        "turns": [
            "Hola Lucie, soy Chopin, el que compró el pase JR. Tengo que ser honesto: te pedí el número porque me gustó tu estilo. Pero me decepcionó un poco que no supieras el horario del shinkansen en Hokkaido.",
            "Hola, Chopin. Lo había entendido.",
            "Entiendes rápido.",
            "¿Estás haciendo tus prácticas de tres años en JTB?",
            "¿Cuarto año?",
            "Duro.",
            "Pensé que en cuarto año uno haría algo distinto a recibir clientes.",
            "Hago otras cosas. Hago [cosas poco útiles]. Hay uno o dos clientes al día.",
            "Por eso te acuerdas de mí.",
            "No solo por eso... Eres un chico muy agradable. Seguro tenemos muchas cosas en común. Pero para evitar malentendidos: tengo novio. Y quizá no debí darte mi número...",
            "Lo siento.",
            "Entonces vas a tener que dejar a tu novio.",
            "Jaja...",
            "No, lo siento.",
            "Me halagas mucho. Tuve un momento de locura y ahora me arrepiento.",
            "¿'Locura'?",
        ],
    },
    "3g579g": {
        "title_es": "Más de 8 meses usando Tinder en 6 países: experiencias, consejos y aprendizajes",
        "context_es": "Caso mixto: contiene diálogo real, pero también mucho comentario del autor. Útil solo como material secundario.",
        "quality_note_es": "No usar como ejemplo principal de Natalia; tiene contenido sexual y partes narrativas mezcladas.",
        "turns": [
            "Deja de preocuparte tanto por el resultado y disfruta. Cuando dejé de querer obtener algo de ellas, más empezaron ellas a querer algo de mí. Por ejemplo, una chica la semana pasada, después de nuestra segunda cita, me dijo: '¿Oye, cuándo me vas a besar?'. De verdad no me importaba tanto el resultado, y creo que esa actitud se vuelve más fácil cuando tienes más opciones. Es una lógica difícil de entender hasta que la vives.",
            "¿Te vas a quedar esta noche?",
            "No, tengo trabajo después de esto.",
            "Entonces supongo que no tendremos sexo por primera vez.",
            "No. Entonces detengo el juego previo y agarro mi ropa.",
            "¿Seguro que no puedes quedarte?",
            "Estoy seguro.",
            "(Después de provocarla sexualmente) ¡Ve a buscarlo ahora! Se refería a los condones. En resumen: algunas chicas fueron encuentros de una noche, una necesitó seis citas y la mayoría tomó tres o cuatro. Si estoy disfrutando, las cosas fluyen.",
        ],
    },
    "423cfd": {
        "title_es": "Reporte de campo número 2: martes",
        "context_es": "Conversación corta con tensión y marco claro sobre qué busca cada persona.",
        "quality_note_es": "Apto con cautela: sirve para estudiar límites, intención y escalada verbal sin ser agresivo.",
        "turns": [
            "¿Qué buscas por aquí?",
            "Aventuras de una noche no, eso seguro.",
            "Eso fue directo. ¿Asumes que eso es lo que yo busco?",
            "Jaja, no sé, muchos hombres sí.",
            "Bueno, supongo que una chica tiene que mantener la guardia arriba.",
            "Sí. Solo me da pesar por los buenos chicos que terminan pagando por eso.",
            "No existen los chicos buenos ni las chicas buenas. Todos somos un poco egoístas. La conversación siguió un rato y luego propuse la cita diciendo que me gustaría continuar esto en persona. Le pregunté si estaba de acuerdo o si la guardia seguía arriba. Ella respondió con su número.",
        ],
    },
    "bex6xv": {
        "title_es": "Desahogo sobre mi última cita de Tinder con una chica",
        "context_es": "Caso de cita con falta de respeto por el tiempo y expectativas poco equilibradas.",
        "quality_note_es": "Apto para Coach: buen ejemplo de límites, dignidad y cuándo no perseguir.",
        "turns": [
            "¿Tierra llamando a Rachel? (su nombre)",
            "Perdón, voy a llegar tarde. Llego a las 6:30. (Habíamos quedado a las 5).",
            "Lo siento, me voy. Los dos acordamos una hora específica e incluso te pregunté si de verdad podías hoy.",
            "¿Y si salgo de la casa y me arreglo ahora, me esperas? Al final pensé: ya vine hasta acá, y la esperé otra hora como un idiota. Terminó llegando dos horas tarde, una falta de respeto total hacia mí y mi tiempo.",
            "No sé qué decir... Deja de ser tan duro. Tienes carro el fin de semana y tampoco es que tengas otras cosas que hacer. Tienes que esforzarte.",
            "Apreciaría mucho que entiendas que vivimos algo lejos y manejar dos veces seguidas cada fin de semana se me hace pesado. También tengo otras responsabilidades.",
            "Estoy dispuesto a esforzarme, pero también necesito comprensión de tu parte. Así que ahora depende de ti si estás bien con eso.",
            "No me gusta que pongas la responsabilidad en mí todo el tiempo. Si estoy bien con eso, genial; si no, no.",
            "Quiero que luches por mí. Me gustan los hombres que luchan por mí. En ese punto, al escuchar ese audio, me dio risa y decidí que definitivamente no iba a funcionar.",
        ],
    },
    "i4qdzu": {
        "title_es": "Primera cita el viernes, la dejé en casa el domingo y aun así tengo una mala sensación",
        "context_es": "Caso sexual explícito y poco limpio como conversación de chat.",
        "quality_note_es": "No recomendado para entrenar a Natalia; mantener solo como caso descartado o auditoría.",
        "turns": [
            "Dijo que sí, feliz. Fuimos a su parada de bus y le volví a preguntar si de verdad quería que fuera a su casa o si debía tomar mi siguiente bus. Me abrazó y dijo que quería que fuera.",
            "Nos besamos y hubo contacto físico. Avancé poco a poco y ella no pareció oponerse. Después hablamos un rato y le dije que me gustaba provocar y tomar las cosas con calma.",
            "Como no tuvimos sexo, bromeé con que al menos otro lo haría. Ella aceptó y sugirió que volviéramos a mi casa ese día. Yo acepté.",
            "Ella no parecía muy motivada. La acerqué y se puso encima de mí. Nos besamos y hablamos un poco.",
            "Volví a bromear sobre lo poco que ella hacía por mí. Entonces me contó algo íntimo de una relación anterior y le dije que no tenía que estresarse, que podíamos ir con calma.",
        ],
    },
    "eyt480": {
        "title_es": "Me gusta una mamá en Tinder, hablamos de su hijo y no sé qué responder",
        "context_es": "Chat breve y real. Útil para entrenar continuidad de conversación después de una respuesta neutra.",
        "quality_note_es": "Apto para Coach: enseña cómo no quedarse sin tema y cómo avanzar con naturalidad.",
        "turns": [
            "Pasé la tarde con mis amigas y mi bebé.",
            "Qué bien, ¿cuántos años tiene?",
            "Un año y ocho meses.",
            "Lindo, ¿cómo se llama?",
            "Bernardo.",
            "Bonito nombre :D",
            "¡Gracias! Y eso fue todo. Estoy confundido sobre qué hacer después. ¡Ayuda, por favor!",
        ],
    },
    "3kvtcq": {
        "title_es": "Estoy saliendo con una chica; dice que le gusto, pero piensa en otro. ¿Qué hago?",
        "context_es": "Falso positivo parcial: no es chat limpio, es relato con etiquetas sueltas.",
        "quality_note_es": "No recomendado para entrenamiento de Natalia; conservar solo para auditoría.",
        "turns": [
            "Eso me hace pensar que ella no quiso hacer un movimiento porque eran colegas. Pero ahora que él se va a otro trabajo, creo que ella tiene esperanzas.",
            "Ella es una chica fantástica, muy linda, y lo que me gusta es que me calma cuando estoy con ella.",
            "Mi mente se tranquiliza un poco. Pero ella no quiere una relación. Ahora mismo solo quiero pasar tiempo con ella.",
            "Resumen: la chica dice que le gusto, pero ha estado pensando en otro hombre y esos pensamientos son cada vez más frecuentes. Estoy muy confundido.",
        ],
    },
    "4oc8x4": {
        "title_es": "¿Los bots pueden usar tu ubicación?",
        "context_es": "Chat breve que parece bot o cuenta sospechosa; útil para entrenar detección de señales raras.",
        "quality_note_es": "Apto como caso negativo: no es ejemplo de éxito, sino de alerta.",
        "turns": [
            "O sea, solo soy una almohada en Tinder. ¿Tú qué eres?",
            "Bien. Yo también pienso eso.",
            "Espera, ¿qué?",
            "Acabo de terminar con mi novio y la verdad solo busco algo casual. ¿Te apuntas?",
            "¿Seguro? ¿Cuándo y dónde? Luego mencionó un lugar real de mi zona. ¿Es un bot nuevo o tal vez una persona real? Estoy confundido.",
        ],
    },
    "3yonq3": {
        "title_es": "Necesito ayuda para hacer avanzar la conversación",
        "context_es": "Chat mínimo de Tinder. Útil para que el Coach sugiera próximos mensajes.",
        "quality_note_es": "Apto para Nivel 1: ejemplo simple de conversación estancada.",
        "turns": [
            "Jaja, ¿qué tal?",
            "Jaja, no mucho.",
            "¿Eres de Nueva York?",
            "Long Island. Ella parece genial y de verdad quiero conocerla, pero no sé cómo avanzar la conversación. Cualquier ayuda se agradece.",
        ],
    },
}


def ensure_table(conn):
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


def translated_items(source):
    items = []
    for item in source["results"]:
        tr = TRANSLATIONS[item["post_id"]]
        turns_es = []
        for original, text_es in zip(item["turns"], tr["turns"]):
            turns_es.append({"speaker": original["speaker"], "text_es": text_es})
        items.append({**item, "translation": {**tr, "turns_es": turns_es}})
    return items


def save_db(items):
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
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
                    tr["title_es"],
                    item.get("body", ""),
                    tr["context_es"],
                    json.dumps(item["turns"], ensure_ascii=False),
                    json.dumps(tr["turns_es"], ensure_ascii=False),
                    item["quality_score"],
                    tr["quality_note_es"],
                    "candidato_traducido_latam",
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def write_outputs(items):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RAW_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.json"
    csv_path = DOCS_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.csv"
    html_path = DOCS_DIR / f"reddit_dialogues_text_top10_latam_{stamp}.html"

    json_path.write_text(json.dumps({"source": str(SOURCE), "results": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "post_id", "subreddit", "quality_score", "title_es", "status"])
        for rank, item in enumerate(items, 1):
            writer.writerow([rank, item["post_id"], item["subreddit"], item["quality_score"], item["translation"]["title_es"], "candidato_traducido_latam"])

    cards = []
    for rank, item in enumerate(items, 1):
        tr = item["translation"]
        turns_html = "".join(
            f"<div class='turn {turn['speaker']}'><b>{'Hombre' if turn['speaker'] == 'hombre' else 'Mujer'}</b><p>{html.escape(turn['text_es'])}</p></div>"
            for turn in tr["turns_es"]
        )
        cards.append(
            f"""
            <article class="case">
              <div class="rank">#{rank}</div>
              <div class="meta">
                <span>r/{html.escape(item['subreddit'])}</span>
                <span>{len(tr['turns_es'])} turnos traducidos</span>
                <span>Score: {item['quality_score']}</span>
                <span>DB: candidato traducido</span>
              </div>
              <h2>{html.escape(tr['title_es'])}</h2>
              <a href="{html.escape(item['url'])}" target="_blank" rel="noreferrer">Abrir fuente original</a>
              <p class="context">{html.escape(tr['context_es'])}</p>
              <section class="dialogue">{turns_html}</section>
              <p class="note">{html.escape(tr['quality_note_es'])}</p>
              <details><summary>Original en inglés</summary><p>{html.escape(item.get('body', '')[:2400])}</p></details>
            </article>
            """
        )

    doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Easy Date - Diálogos Reddit traducidos LATAM</title>
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
  </style>
</head>
<body>
  <header>
    <h1>Conversaciones traducidas a español latino</h1>
    <div class="summary">
      Texto visible corregido en español latino. La base conserva original y traducción en <code>reddit_dialogue_text_candidates</code>.
    </div>
  </header>
  <main>{''.join(cards)}</main>
</body>
</html>
"""
    html_path.write_text(doc, encoding="utf-8")
    return {"html": str(html_path), "csv": str(csv_path), "json": str(json_path)}


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    items = translated_items(source)
    save_db(items)
    paths = write_outputs(items)
    print(json.dumps({"count": len(items), "paths": paths}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
