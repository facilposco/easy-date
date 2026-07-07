import csv
import html
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend import server  # noqa: E402


QUESTIONS = [
    ("text_game", "Como pido WhatsApp sin parecer necesitado?"),
    ("text_game", "Cuando conviene pasar de chat a cita?"),
    ("text_game", "Que hago si ella responde frio pero no me rechaza?"),
    ("text_game", "Que tipo de abridor gracioso funciona mejor?"),
    ("text_game", "Como cierro una cita con vino o cafe sin sonar intenso?"),
    ("text_game", "Como manejo una respuesta tardia de varias horas?"),
    ("text_game", "Cuantos emojis conviene usar en un mensaje inicial?"),
    ("text_game", "Que senales muestran que ella esta receptiva?"),
    ("text_game", "Como responder si ella dice jaja y nada mas?"),
    ("text_game", "Que errores hacen perder una conversacion que iba bien?"),
    ("seduccion", "Como evitar sobreinvertir al inicio?"),
    ("seduccion", "Que significa calibrar el tono con una mujer selectiva?"),
    ("seduccion", "Como crear curiosidad sin presumir?"),
    ("seduccion", "Que temas ayudan a una primera cita?"),
    ("seduccion", "Como detectar si ya puedo proponer plan?"),
    ("seduccion", "Como responder a una prueba o comentario defensivo?"),
    ("seduccion", "Que diferencia hay entre humor y payasear?"),
    ("seduccion", "Como pedir Instagram en vez de numero?"),
    ("seduccion", "Que hago si ella tiene muchos matches?"),
    ("seduccion", "Como mantener la conversacion humana y no entrevista?"),
]


def summarize_case(case: dict) -> str:
    text = server.clean_ui_text(case.get("text", ""))
    lines = [line for line in text.splitlines() if line.strip()]
    interesting = []
    for line in lines:
        low = server.analysis_text(line)
        if any(token in low for token in ["whatsapp", "numero", "telefono", "cita", "date", "jaja", "cafe", "vino", "plan"]):
            interesting.append(line[:180])
    if not interesting:
        interesting = lines[:2]
    return " | ".join(interesting[:2])[:300]


def grounded_answer(question: str, success_cases: list[dict], book_cases: list[dict], old_cases: list[dict]) -> str:
    q = server.analysis_text(question)
    evidence_count = len(success_cases) + len(book_cases) + len(old_cases)
    if evidence_count == 0:
        return "Sin evidencia suficiente en el RAG consultado; no conviene inventar una regla."

    if any(token in q for token in ["whatsapp", "numero", "telefono", "instagram"]):
        return (
            "Pide contacto despues de una senal clara de receptividad o despues de aterrizar un plan. "
            "La evidencia recuperada favorece una razon simple y concreta, no pedirlo en frio."
        )
    if any(token in q for token in ["cita", "plan", "cafe", "vino"]):
        return (
            "Avanza a cita cuando ya hay ritmo, humor o respuesta abierta. Propone un plan facil "
            "con dia/lugar ligero y deja una salida comoda."
        )
    if any(token in q for token in ["abridor", "gracioso", "humor", "jaja", "payasear"]):
        return (
            "El humor funciona cuando conecta con el contexto y abre conversacion. Si solo busca llamar "
            "la atencion o se vuelve personaje, baja la calidad."
        )
    if any(token in q for token in ["frio", "defensivo", "selectiva", "matches"]):
        return (
            "Con una mujer fria o selectiva, baja intensidad, responde al contexto y usa curiosidad corta. "
            "No persigas aprobacion ni expliques demasiado."
        )
    if any(token in q for token in ["emoji", "emojis"]):
        return (
            "Usa 0 a 2 emojis como maximo si aportan tono. Muchos emojis o emojis sexuales tempranos "
            "se leen como descalibrados."
        )
    if any(token in q for token in ["entrevista", "humana", "sobreinvertir", "curiosidad", "presumir"]):
        return (
            "Mantenerlo humano significa una idea clara por turno, responder lo ultimo que ella dijo y "
            "dejar espacio para que ella tambien invierta."
        )
    return (
        "La pauta consistente es calibrar: mensaje corto, conectado al contexto visible, con avance suave "
        "solo cuando hay receptividad."
    )


def run() -> list[dict]:
    rows = []
    for category, question in QUESTIONS:
        success_cases = server.retrieve_success_chroma_cases(question, limit=3)
        if not success_cases:
            success_cases = server.retrieve_success_sqlite_cases(question, limit=2)
        book_cases = server.retrieve_books_chroma_cases(question, limit=2)
        old_cases = server.retrieve_chroma_cases(question, "coqueta", limit=1)
        answer = grounded_answer(question, success_cases, book_cases, old_cases)
        sources = []
        for case in success_cases[:3] + book_cases[:2] + old_cases[:1]:
            sources.append(f"{case.get('source')}:{case.get('post_id')}")
        rows.append(
            {
                "categoria": category,
                "pregunta": question,
                "respuesta_grounded": answer,
                "success_cases": len(success_cases),
                "book_cases": len(book_cases),
                "old_cases": len(old_cases),
                "fuentes": ", ".join(sources),
                "muestra_evidencia": summarize_case((success_cases + book_cases + old_cases)[0])
                if (success_cases + book_cases + old_cases)
                else "",
                "resultado": "OK" if sources else "SIN_EVIDENCIA",
            }
        )
    return rows


def write_reports(rows: list[dict]) -> dict:
    docs = ROOT_DIR / "docs"
    docs.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = docs / f"natalia_rag_qa_20_{stamp}.csv"
    json_path = docs / f"natalia_rag_qa_20_{stamp}.json"
    html_path = docs / f"natalia_rag_qa_20_{stamp}.html"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    table_rows = "\n".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in ["categoria", "pregunta", "respuesta_grounded", "fuentes", "resultado"]
        )
        + "</tr>"
        for row in rows
    )
    html_path.write_text(
        f"""<!doctype html>
<html lang="es"><meta charset="utf-8"><title>QA Natalia RAG 20</title>
<style>
body{{font-family:Arial,sans-serif;background:#10131a;color:#eef2ff;margin:24px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
td,th{{border:1px solid #2e3445;padding:10px;vertical-align:top}}
th{{background:#1f2635}} tr:nth-child(even){{background:#151b27}}
.ok{{color:#43d17a}}
</style>
<h1>QA Natalia RAG - 20 preguntas</h1>
<p>Respuestas generadas con recuperacion RAG y fuentes; sin afirmar datos fuera de evidencia.</p>
<table><thead><tr><th>Categoria</th><th>Pregunta</th><th>Respuesta grounded</th><th>Fuentes</th><th>Resultado</th></tr></thead>
<tbody>{table_rows}</tbody></table></html>""",
        encoding="utf-8",
    )
    return {"csv": str(csv_path), "json": str(json_path), "html": str(html_path)}


if __name__ == "__main__":
    rows = run()
    paths = write_reports(rows)
    print(json.dumps({"paths": paths, "rows": rows}, ensure_ascii=False, indent=2))
