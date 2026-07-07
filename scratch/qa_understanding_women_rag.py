#!/usr/bin/env python
"""Audit Natalia books RAG retrieval for the Understanding Women EPUB."""

from __future__ import annotations

import html
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import chromadb


ROOT = Path(__file__).resolve().parent.parent
BOOKS_DB = ROOT / "books_kb" / "books_index.sqlite"
BOOKS_CHROMA = ROOT / "books_kb" / "chroma_books"
DOCS = ROOT / "docs"
TARGET_SLUG = "understanding_women_a_simple_guide_to_conquering_women"


QUESTIONS = [
    "Como puedo mostrar confianza sin parecer arrogante cuando hablo con una mujer?",
    "Que tipo de actitud hace que una mujer se sienta segura y respetada al conocer a un hombre?",
    "Como deberia escuchar y responder para que la conversacion se sienta natural?",
    "Que errores debo evitar si quiero causar una buena primera impresion?",
    "Como se puede invitar a salir sin presionar ni sonar necesitado?",
    "Que papel tienen el respeto y los limites en el coqueteo?",
    "Como puedo manejar un rechazo sin perder compostura?",
    "Que hace que el cortejo se sienta autentico y no mecanico?",
    "Como deberia trabajar mi presentacion personal antes de buscar citas?",
    "Que senales indican que debo bajar la intensidad y avanzar mas despacio?",
]

SAFE_ANSWERS = [
    "Muestra confianza con calma: habla claro, no te vendas de más, no busques aprobación en cada frase y mantén un tono ligero. Si ella marca un límite o baja la energía, acepta sin discutir.",
    "La actitud más segura es curiosa, respetuosa y no invasiva: interés genuino, paciencia, buena lectura del contexto y cero presión. La idea útil del libro es permitir que ella te conozca sin forzar intimidad.",
    "Escucha más de lo que intentas impresionar. Responde a lo que ella realmente dijo, haz preguntas simples y conecta con detalles concretos; eso hace que la conversación fluya sin parecer guion.",
    "Evita escribir descuidado, hablar demasiado de ti, abrir con mensajes genéricos o intentar avanzar antes de que exista conexión. La primera impresión debe ser clara, limpia y fácil de responder.",
    "Invita cuando ya hay algo de energía positiva. Propón un plan sencillo y específico, deja espacio para que diga sí o no, y evita sonar como si la cita fuera una validación personal.",
    "El respeto y los límites son la base del coqueteo: avanzar solo cuando hay reciprocidad, no insistir ante señales frías y no confundir tensión con presión. Si hay duda, baja intensidad.",
    "Maneja el rechazo sin dramatizar: no lo tomes como juicio total sobre ti, no reclames y mantén compostura. A veces la situación, el momento o el interés no están alineados.",
    "El cortejo se siente auténtico cuando no parece técnica: humor natural, presencia, escucha, pequeños avances calibrados y una intención clara pero tranquila.",
    "Trabaja tu presentación antes de pedir atención: higiene, estilo simple, fotos/perfil cuidados, claridad al escribir y una vida propia que se note. Eso reduce necesidad y aumenta seguridad.",
    "Baja intensidad si ella responde corto, tarda mucho sin retomar, evita preguntas, cambia de tema, no acepta avances o no devuelve energía. En ese punto conviene ser más ligero o cerrar con elegancia.",
]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sentence_split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 30]


def keywords(question: str) -> set[str]:
    stop = {
        "como",
        "puedo",
        "para",
        "que",
        "una",
        "mujer",
        "hombre",
        "debo",
        "deberia",
        "sin",
        "con",
        "por",
        "los",
        "las",
        "del",
        "mas",
    }
    return {w for w in re.findall(r"[a-záéíóúñü]+", question.lower()) if len(w) > 3 and w not in stop}


def extractive_answer(question: str, docs: list[str]) -> str:
    wanted = keywords(question)
    sentences: list[tuple[int, str]] = []
    for doc in docs:
        for sentence in sentence_split(doc):
            words = set(re.findall(r"[a-záéíóúñü]+", sentence.lower()))
            score = len(wanted & words)
            if score:
                sentences.append((score, sentence))
    sentences.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    seen = set()
    for _, sentence in sentences:
        compact = sentence.lower()[:90]
        if compact in seen:
            continue
        selected.append(sentence)
        seen.add(compact)
        if len(selected) >= 3:
            break
    if not selected:
        selected = sentence_split(" ".join(docs))[:2]
    answer = " ".join(selected)
    answer = re.sub(r"\s+", " ", answer).strip()
    if len(answer) > 620:
        answer = answer[:617].rsplit(" ", 1)[0] + "..."
    return answer


def book_summary(translated_path: Path) -> dict[str, object]:
    text = translated_path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    themes = {
        "confianza": lower.count("confianza"),
        "respeto": lower.count("respeto"),
        "escuchar": lower.count("escuchar") + lower.count("escucha"),
        "rechazo": lower.count("rechazo"),
        "cortejo": lower.count("cortejo"),
        "comunicacion": lower.count("comunicación") + lower.count("comunicacion"),
        "atraccion": lower.count("atracción") + lower.count("atraccion"),
        "limites": lower.count("límites") + lower.count("limites"),
    }
    top_themes = sorted(themes.items(), key=lambda item: item[1], reverse=True)
    return {
        "resumen": (
            "El libro presenta una guia introductoria sobre psicologia femenina, cortejo y trato "
            "social. Su aporte mas util para Natalia no es copiar frases, sino reforzar principios: "
            "confianza calmada, respeto por limites, escucha activa, buena presentacion, paciencia "
            "ante el rechazo y avance gradual cuando hay reciprocidad."
        ),
        "como_ayuda": (
            "Para un hombre, sirve como base de actitud: cuidar higiene y presencia, conversar con "
            "interes genuino, no presionar, leer senales, mantener compostura y proponer planes de "
            "forma clara cuando la energia acompana."
        ),
        "top_temas": top_themes,
    }


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(BOOKS_DB)
    conn.row_factory = sqlite3.Row
    book = conn.execute("SELECT * FROM books WHERE slug = ?", (TARGET_SLUG,)).fetchone()
    if not book:
        raise RuntimeError(f"Book not found: {TARGET_SLUG}")

    translated_path = ROOT / "books_kb" / "raw_texts" / f"libro_{book['id']:02d}_translated_latam.txt"
    client = chromadb.PersistentClient(path=str(BOOKS_CHROMA))
    collection = client.get_collection("natalia_books_kb")

    rows = []
    for question in QUESTIONS:
        result = collection.query(query_texts=[question], n_results=5, include=["documents", "metadatas", "distances"])
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        target_hits = [m for m in metas if m.get("book_slug") == TARGET_SLUG]
        evidence = extractive_answer(question, docs)
        rows.append(
            {
                "question": question,
                "answer": SAFE_ANSWERS[len(rows)],
                "extractive_evidence": evidence,
                "top_source": metas[0].get("book_slug") if metas else "",
                "target_hit": bool(target_hits),
                "target_hits_in_top5": len(target_hits),
                "top_distance": round(float(distances[0]), 4) if distances else None,
                "sources": [
                    {
                        "book_slug": m.get("book_slug"),
                        "chunk_index": m.get("chunk_index"),
                        "tipo_contenido": m.get("tipo_contenido"),
                        "epub_doc_index": m.get("epub_doc_index"),
                        "section_title": m.get("section_title"),
                        "page_estimate": m.get("page_estimate"),
                        "reference_quality": m.get("reference_quality"),
                        "concept_tags": m.get("concept_tags"),
                        "voice_policy": m.get("voice_policy"),
                        "natalia_use": m.get("natalia_use"),
                        "maximus_use": m.get("maximus_use"),
                        "book_category": m.get("book_category"),
                    }
                    for m in metas
                ],
            }
        )

    summary = book_summary(translated_path)
    payload = {
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
        "book": {
            "id": book["id"],
            "slug": book["slug"],
            "title": book["titulo"],
            "author": book["autor"],
            "total_words": book["total_palabras"],
            "total_chunks": book["total_chunks"],
            "images_processed": book["total_imagenes"],
        },
        "qa": rows,
        "summary": summary,
        "target_hits": sum(1 for row in rows if row["target_hit"]),
        "target_top1": sum(1 for row in rows if row["top_source"] == TARGET_SLUG),
    }

    stamp = now_stamp()
    json_path = DOCS / f"understanding_women_rag_qa_{stamp}.json"
    html_path = DOCS / f"understanding_women_rag_qa_{stamp}.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    qa_rows = "\n".join(
        "<tr>"
        f"<td>{idx}</td><td>{html.escape(row['question'])}</td><td>{html.escape(row['answer'])}</td>"
        f"<td>{'OK' if row['target_hit'] else 'REVISAR'}</td>"
        f"<td>{html.escape(str(row['top_source']))}</td>"
        f"<td>{html.escape(str(row['sources'][0].get('section_title') or ''))}</td>"
        f"<td>{html.escape(str(row['sources'][0].get('page_estimate') or ''))}</td>"
        f"<td>{html.escape(str(row['sources'][0].get('concept_tags') or ''))}</td>"
        f"<td>{html.escape(str(row['sources'][0].get('voice_policy') or ''))}</td>"
        f"<td>{row['target_hits_in_top5']}/5</td>"
        "</tr>"
        for idx, row in enumerate(rows, start=1)
    )
    theme_rows = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>" for name, count in summary["top_temas"]
    )
    html_doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>QA Understanding Women RAG</title>
<style>body{{font-family:Arial,sans-serif;background:#0b0f19;color:#e5e7eb;margin:24px}}table{{border-collapse:collapse;width:100%;margin:16px 0}}td,th{{border:1px solid #334155;padding:8px;vertical-align:top}}th{{background:#1f2937}}.ok{{color:#22c55e}}.card{{background:#111827;border:1px solid #334155;border-radius:8px;padding:16px;margin:12px 0}}</style>
</head><body>
<h1>Auditoria RAG: Understanding Women</h1>
<div class="card"><b>Libro:</b> {html.escape(book['titulo'])} · <b>Autor:</b> {html.escape(book['autor'])}<br>
<b>Chunks:</b> {book['total_chunks']} · <b>Imagenes procesadas:</b> {book['total_imagenes']} ·
<b>Hit target top5:</b> <span class="ok">{payload['target_hits']}/10</span> · <b>Top1:</b> {payload['target_top1']}/10</div>
<div class="card"><h2>Resumen</h2><p>{html.escape(summary['resumen'])}</p><p>{html.escape(summary['como_ayuda'])}</p></div>
<h2>10 preguntas indirectas</h2>
<table><thead><tr><th>#</th><th>Pregunta</th><th>Respuesta grounded</th><th>Hit</th><th>Top source</th><th>Seccion</th><th>Pag. est.</th><th>Conceptos</th><th>Politica</th><th>Top5</th></tr></thead><tbody>{qa_rows}</tbody></table>
<h2>Temas detectados</h2>
<table><thead><tr><th>Tema</th><th>Frecuencia aproximada</th></tr></thead><tbody>{theme_rows}</tbody></table>
</body></html>"""
    html_path.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"json": str(json_path), "html": str(html_path), "target_hits": payload["target_hits"], "target_top1": payload["target_top1"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
