#!/usr/bin/env python
"""Generate a grounded tips report from the last ingested Understanding Women book."""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

import chromadb


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BOOKS_CHROMA = ROOT / "books_kb" / "chroma_books"
BOOK_SLUG = "understanding_women_a_simple_guide_to_conquering_women"

TIPS = [
    {
        "query": "confianza sin arrogancia hablar con mujeres",
        "tip": "Confianza tranquila: habla claro, evita presumir y no busques aprobación en cada frase.",
        "why": "El libro insiste en que la seguridad se percibe mejor cuando el hombre tiene presencia propia y no actúa desde necesidad.",
    },
    {
        "query": "escuchar conversar no hablar demasiado",
        "tip": "Escucha activa: responde a lo que ella dijo, no a lo que querías decir de antemano.",
        "why": "La conversación natural nace de escuchar, hacer preguntas simples y sostener el hilo sin monólogo.",
    },
    {
        "query": "primera impresion escribir claro ortografia citas online",
        "tip": "Primera impresión limpia: escribe claro, cuida ortografía y abre con algo fácil de responder.",
        "why": "En apps, el mensaje inicial compite por atención; claridad y cuidado reducen fricción.",
    },
    {
        "query": "presentacion personal perfil fotos higiene vestir",
        "tip": "Presentación antes de seducción: cuida higiene, estilo, fotos y perfil antes de pedir atención.",
        "why": "El libro conecta atracción con señales visibles de autocuidado y coherencia personal.",
    },
    {
        "query": "invitar a salir cita plan sin presionar",
        "tip": "Invita cuando ya hay energía: propone un plan concreto y deja espacio para que ella elija.",
        "why": "Un cierre funciona mejor cuando llega después de conexión, no como presión temprana.",
    },
    {
        "query": "rechazo timidez compostura hablar mujeres",
        "tip": "No dramatices el rechazo: trátalo como información, no como sentencia sobre tu valor.",
        "why": "El libro sugiere relativizar el rechazo para mantener compostura y seguir aprendiendo.",
    },
    {
        "query": "ritmo intensidad avanzar despacio señales",
        "tip": "Calibra intensidad: si ella responde frío o no devuelve energía, baja velocidad.",
        "why": "La escalada social debe sentirse gradual; avanzar sin reciprocidad rompe confianza.",
    },
    {
        "query": "respeto limites presion coqueteo",
        "tip": "Respeto como base: el coqueteo debe sentirse ligero, no invasivo ni insistente.",
        "why": "La parte útil para Natalia es usar límites como guardrail: avanzar solo con señales positivas.",
    },
    {
        "query": "vida social pasiones circulo social atractivo",
        "tip": "Construye vida propia: pasiones, círculo social y planes reales hacen que no dependas del chat.",
        "why": "El libro asocia atractivo con tener una vida activa, no con perseguir validación.",
    },
    {
        "query": "autenticidad cortejo no mecanico humor natural",
        "tip": "No suenes a técnica: usa humor natural, curiosidad y presencia en vez de fórmulas rígidas.",
        "why": "El aprendizaje debe volverse criterio silencioso; Natalia no debe repetir teoría, sino sonar humana.",
    },
]


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    collection = chromadb.PersistentClient(path=str(BOOKS_CHROMA)).get_collection("natalia_books_kb")
    rows = []
    for index, item in enumerate(TIPS, start=1):
        result = collection.query(query_texts=[item["query"]], n_results=5, include=["metadatas", "documents"])
        metas = result.get("metadatas", [[]])[0]
        target = next((meta for meta in metas if meta.get("book_slug") == BOOK_SLUG), metas[0] if metas else {})
        rows.append(
            {
                "index": index,
                **item,
                "book_slug": target.get("book_slug"),
                "section_title": target.get("section_title"),
                "page_estimate": target.get("page_estimate"),
                "epub_doc_index": target.get("epub_doc_index"),
                "concept_tags": target.get("concept_tags"),
                "voice_policy": target.get("voice_policy"),
                "natalia_use": target.get("natalia_use"),
                "maximus_use": target.get("maximus_use"),
            }
        )
    payload = {
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
        "book_slug": BOOK_SLUG,
        "title": "Understanding Women: A Simple Guide to Conquering Women",
        "note": "Tips sintetizados para uso seguro; no son citas literales.",
        "tips": rows,
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = DOCS / f"understanding_women_top10_tips_{stamp}.json"
    html_path = DOCS / f"understanding_women_top10_tips_{stamp}.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    trs = "\n".join(
        "<tr>"
        f"<td>{row['index']}</td>"
        f"<td>{html.escape(row['tip'])}</td>"
        f"<td>{html.escape(row['why'])}</td>"
        f"<td>{html.escape(str(row.get('section_title') or ''))}</td>"
        f"<td>{html.escape(str(row.get('page_estimate') or ''))}</td>"
        f"<td>{html.escape(str(row.get('concept_tags') or ''))}</td>"
        f"<td>{html.escape(str(row.get('voice_policy') or ''))}</td>"
        "</tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Top 10 Understanding Women</title>
<style>body{{font-family:Arial,sans-serif;background:#0b0f19;color:#e5e7eb;margin:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #334155;padding:8px;vertical-align:top}}th{{background:#1f2937}}.note{{color:#fbbf24}}</style>
</head><body><h1>Top 10 tips para Natalia/Maximus</h1>
<p><b>Libro:</b> Understanding Women: A Simple Guide to Conquering Women</p>
<p class="note">Sintesis segura basada en recuperacion RAG; no son citas literales.</p>
<table><thead><tr><th>#</th><th>Tip</th><th>Por que sirve</th><th>Seccion</th><th>Pag. est.</th><th>Conceptos</th><th>Politica</th></tr></thead><tbody>{trs}</tbody></table>
</body></html>"""
    html_path.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"json": str(json_path), "html": str(html_path), "tips": len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
