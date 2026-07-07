from __future__ import annotations

import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.server import TEXTGAME_CONCEPT_PATTERNS, clean_ui_text, retrieve_books_chroma_cases


DB_PATH = PROJECT_ROOT / "textgame.db"
DOCS_DIR = PROJECT_ROOT / "docs"


def fetch_success_cases(concept: str, tokens: List[str], limit: int = 4) -> List[Dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    query = """
        SELECT post_id, title_es, summary_es, translation_es, score, objectives_json, source_url
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
        ORDER BY score DESC, created_at DESC
    """
    rows: List[Dict[str, Any]] = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(query):
            text = clean_ui_text(
                " ".join(
                    str(row[key] or "")
                    for key in ["title_es", "summary_es", "translation_es", "objectives_json"]
                )
            ).lower()
            if any(token.lower() in text for token in tokens):
                rows.append(dict(row))
            if len(rows) >= limit:
                break
    return rows


def compact(text: str, limit: int = 220) -> str:
    value = clean_ui_text(text)
    return value if len(value) <= limit else value[:limit].rstrip() + "..."


def build_graph() -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    seen_nodes = set()

    def add_node(node_id: str, label: str, kind: str, **extra: Any) -> None:
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append({"id": node_id, "label": label, "kind": kind, **extra})

    add_node("agent:natalia", "Natalia Persona", "agent")
    add_node("agent:maximus", "Maximus Coach", "agent")

    for concept, tokens in TEXTGAME_CONCEPT_PATTERNS.items():
        concept_id = f"concept:{concept}"
        add_node(concept_id, concept, "concept", tokens=tokens)
        edges.append({"source": concept_id, "target": "agent:natalia", "relation": "silent_strategy"})
        edges.append({"source": concept_id, "target": "agent:maximus", "relation": "teachable_principle"})

        books = retrieve_books_chroma_cases(f"{concept} {' '.join(tokens)} text game dating", limit=2)
        for index, book in enumerate(books, start=1):
            book_id = f"book:{concept}:{index}:{book.get('post_id') or index}"
            add_node(
                book_id,
                f"Libro: {concept} #{index}",
                "book_principle",
                source=book.get("source", ""),
                text=compact(book.get("text", ""), 420),
            )
            edges.append({"source": book_id, "target": concept_id, "relation": "supports"})

        cases = fetch_success_cases(concept, tokens)
        for index, case in enumerate(cases, start=1):
            case_id = f"case:{concept}:{case.get('post_id') or index}"
            title = clean_ui_text(case.get("title_es") or f"Caso {case.get('post_id') or index}")
            add_node(
                case_id,
                title or f"Caso {index}",
                "success_case",
                post_id=case.get("post_id"),
                score=case.get("score"),
                url=case.get("source_url"),
                summary=compact(case.get("summary_es") or case.get("translation_es") or "", 320),
            )
            edges.append({"source": case_id, "target": concept_id, "relation": "example_of"})
            response_id = f"response:{concept}:{case.get('post_id') or index}"
            add_node(
                response_id,
                f"Respuesta Natalia derivada: {concept}",
                "natalia_response_pattern",
                rule="Usar el principio en silencio y responder como mujer real, sin teoria visible.",
            )
            edges.append({"source": concept_id, "target": response_id, "relation": "guides"})
            edges.append({"source": case_id, "target": response_id, "relation": "grounds"})

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "description": "Grafo auditable libro -> principio -> caso real -> patron de respuesta Natalia.",
        "nodes": nodes,
        "edges": edges,
    }


def write_html(graph: Dict[str, Any], html_path: Path) -> None:
    concept_sections = []
    nodes_by_kind: Dict[str, List[Dict[str, Any]]] = {}
    for node in graph["nodes"]:
        nodes_by_kind.setdefault(node["kind"], []).append(node)

    for concept in nodes_by_kind.get("concept", []):
        concept_id = concept["id"]
        related_edges = [edge for edge in graph["edges"] if edge["target"] == concept_id or edge["source"] == concept_id]
        related_ids = {edge["source"] for edge in related_edges} | {edge["target"] for edge in related_edges}
        related_nodes = [node for node in graph["nodes"] if node["id"] in related_ids and node["id"] != concept_id]
        cards = "\n".join(
            f"<article><strong>{html.escape(node['kind'])}</strong><h3>{html.escape(node['label'])}</h3>"
            f"<p>{html.escape(str(node.get('summary') or node.get('text') or node.get('rule') or ''))}</p></article>"
            for node in related_nodes
        )
        concept_sections.append(
            f"<section><h2>{html.escape(concept['label'])}</h2><p>Tokens: {html.escape(', '.join(concept.get('tokens', [])))}</p><div class='grid'>{cards}</div></section>"
        )

    html_doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Grafo Natalia: libros, principios y casos</title>
<style>
body{{font-family:Arial,sans-serif;background:#0b0f17;color:#e8eefc;margin:0;padding:24px}}
h1{{margin-top:0}} section{{border:1px solid #263244;border-radius:8px;margin:18px 0;padding:18px;background:#121923}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
article{{background:#080c12;border:1px solid #28364a;border-radius:8px;padding:12px}}
strong{{color:#ff4f8b}} h3{{margin:.4rem 0}} p{{line-height:1.45;color:#cbd6ea}}
code{{color:#8cc8ff}}
</style>
</head>
<body>
<h1>Grafo Natalia: libro -> principio -> caso real -> respuesta</h1>
<p>Generado: <code>{html.escape(graph['generated_at'])}</code>. Este grafo organiza evidencia; no inventa conversaciones ni reemplaza Chroma.</p>
{''.join(concept_sections)}
</body>
</html>"""
    html_path.write_text(html_doc, encoding="utf-8")


def main() -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    graph = build_graph()
    json_path = DOCS_DIR / f"natalia_learning_graph_{stamp}.json"
    html_path = DOCS_DIR / f"natalia_learning_graph_{stamp}.html"
    json_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(graph, html_path)
    print(json.dumps({"json": str(json_path), "html": str(html_path), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
