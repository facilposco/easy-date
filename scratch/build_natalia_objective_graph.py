import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "textgame.db"
DOCS_DIR = ROOT_DIR / "docs"


def clean(value):
    return " ".join(str(value or "").replace("\x00", " ").split())


def parse_list(raw):
    try:
        data = json.loads(raw or "[]")
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [clean(item) for item in data if clean(item)]


def normalize_objective(value):
    text = clean(value).lower()
    if any(token in text for token in ["whatsapp", "phone", "telefono", "teléfono", "numero", "número"]):
        return "contacto"
    if "instagram" in text or "insta" in text:
        return "instagram"
    if "snap" in text:
        return "snapchat"
    if any(token in text for token in ["date", "cita", "meet", "salir", "quedar"]):
        return "cita"
    if any(token in text for token in ["humor", "jaja", "haha", "laugh", "risa"]):
        return "humor"
    if any(token in text for token in ["opener", "abridor", "line"]):
        return "abridor"
    if any(token in text for token in ["connection", "conexion", "conexión"]):
        return "conexion"
    return text or "objetivo_desconocido"


def confidence(row):
    score = int(row["score"] or 0)
    objectives = parse_list(row["objectives_json"])
    text = clean(row["translation_es"] or row["ocr_text"] or "")
    has_url = bool(clean(row["source_url"]))
    has_image = clean(row["local_paths_json"]) not in {"", "[]"}
    strong = sum([bool(objectives), score >= 8, len(text.split()) >= 35, has_url, has_image])
    if strong >= 4:
        return "alta"
    if strong >= 2:
        return "media"
    return "baja"


def main():
    DOCS_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT post_id, title, title_es, subreddit, score, source_url, objectives_json,
               translation_es, ocr_text, local_paths_json
        FROM reddit_success_scrape_candidates
        WHERE status = 'candidate_qa'
        """
    ).fetchall()
    conn.close()

    nodes = {}
    edges = []
    objective_counts = Counter()
    source_counts = Counter()
    confidence_counts = Counter()
    co_occurrence = Counter()

    def add_node(node_id, label, node_type, **attrs):
        nodes[node_id] = {"id": node_id, "label": label, "type": node_type, **attrs}

    for objective in ["contacto", "whatsapp", "instagram", "snapchat", "cita", "humor", "abridor", "conexion"]:
        add_node(f"objective:{objective}", objective, "objective")

    for row in rows:
        post_id = clean(row["post_id"])
        if not post_id:
            continue
        title = clean(row["title_es"] or row["title"] or post_id)
        source = clean(row["subreddit"] or "fuente_desconocida").lower()
        conf = confidence(row)
        objectives = sorted({normalize_objective(item) for item in parse_list(row["objectives_json"])})
        if not objectives:
            objectives = ["objetivo_desconocido"]

        add_node(f"case:{post_id}", title[:90], "case", score=int(row["score"] or 0), confidence=conf)
        add_node(f"source:{source}", source, "source")
        add_node(f"confidence:{conf}", f"confianza {conf}", "confidence")
        edges.append({"source": f"case:{post_id}", "target": f"source:{source}", "relation": "ocurre_en"})
        edges.append({"source": f"case:{post_id}", "target": f"confidence:{conf}", "relation": "tiene_confianza"})
        source_counts[source] += 1
        confidence_counts[conf] += 1

        for objective in objectives:
            add_node(f"objective:{objective}", objective, "objective")
            edges.append({"source": f"case:{post_id}", "target": f"objective:{objective}", "relation": "evidencia_objetivo"})
            objective_counts[objective] += 1
        for index, left in enumerate(objectives):
            for right in objectives[index + 1 :]:
                co_occurrence[tuple(sorted((left, right)))] += 1

    for (left, right), weight in co_occurrence.items():
        edges.append(
            {
                "source": f"objective:{left}",
                "target": f"objective:{right}",
                "relation": "co_ocurre",
                "weight": weight,
            }
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    graph = {
        "generated_at": stamp,
        "source": str(DB_PATH),
        "summary": {
            "cases": len(rows),
            "objectives": dict(objective_counts.most_common()),
            "sources": dict(source_counts.most_common()),
            "confidence": dict(confidence_counts.most_common()),
        },
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    json_path = DOCS_DIR / f"natalia_objective_graph_{stamp}.json"
    html_path = DOCS_DIR / f"natalia_objective_graph_{stamp}.html"
    json_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    top_objectives = "".join(
        f"<tr><td>{objective}</td><td>{count}</td></tr>" for objective, count in objective_counts.most_common()
    )
    top_sources = "".join(f"<tr><td>{source}</td><td>{count}</td></tr>" for source, count in source_counts.most_common())
    html_path.write_text(
        f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Grafo de objetivos Natalia</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#0b0f16; color:#e8eef8; margin:0; padding:32px; }}
    h1, h2 {{ color:#fff; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:18px; }}
    section {{ border:1px solid #273244; border-radius:8px; padding:18px; background:#141a24; }}
    table {{ width:100%; border-collapse:collapse; }}
    td, th {{ border-bottom:1px solid #273244; padding:8px; text-align:left; }}
    .pill {{ display:inline-block; padding:5px 10px; margin:4px; border-radius:999px; background:#1f2c42; }}
  </style>
</head>
<body>
  <h1>Grafo de objetivos Natalia</h1>
  <p>Casos candidate_qa: <strong>{len(rows)}</strong>. JSON auditable: <code>{json_path.name}</code></p>
  <div class="grid">
    <section><h2>Objetivos</h2><table><tr><th>Objetivo</th><th>Casos</th></tr>{top_objectives}</table></section>
    <section><h2>Fuentes</h2><table><tr><th>Fuente</th><th>Casos</th></tr>{top_sources}</table></section>
    <section><h2>Confianza</h2>{"".join(f'<span class="pill">{k}: {v}</span>' for k, v in confidence_counts.most_common())}</section>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(json.dumps({"json": str(json_path), "html": str(html_path), "cases": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
