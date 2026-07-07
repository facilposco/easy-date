from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
BOOKS_DB = ROOT / "books_kb" / "books_index.sqlite"
TEXTGAME_DB = ROOT / "textgame.db"
DOCS = ROOT / "docs"


TAG_PATTERNS: dict[str, list[str]] = {
    "opener": ["abridor", "primer mensaje", "opener", "icebreaker", "apertura", "opening"],
    "humor": ["humor", "gracioso", "broma", "jaja", "risa", "banter", "joke", "funny"],
    "timing": ["timing", "tiempo", "espera", "responder", "demora", "ritmo", "wait", "reply"],
    "cierre": ["whatsapp", "numero", "número", "telefono", "teléfono", "cita", "salir", "plan", "date", "phone"],
    "inversion": ["inversion", "inversión", "invertir", "necesitado", "perseguir", "chase", "investment"],
    "tension": ["tension", "tensión", "coqueteo", "flirteo", "sexual", "atraccion", "atracción", "desire"],
    "frame": ["frame", "marco", "liderazgo", "liderar", "calibrar", "calibracion", "calibración"],
    "perfil": ["foto", "perfil", "bio", "presentacion", "presentación", "apariencia", "profile"],
    "confianza": ["confianza", "seguridad", "calma", "autoestima", "valor", "confidence"],
    "escucha": ["escuchar", "empatía", "empatia", "validar", "preguntar", "atencion", "atención"],
    "limites": ["limite", "límite", "respeto", "consentimiento", "presion", "presión", "rechazo"],
    "psicologia_femenina": ["mujer", "mujeres", "femenina", "emocion", "emoción", "relacion", "relación"],
}

SUPER_TAG_MAP: dict[str, str] = {
    "opener": "humor_tension_sana",
    "humor": "humor_tension_sana",
    "tension": "humor_tension_sana",
    "frame": "valor_congruencia",
    "inversion": "reciprocidad_inversion",
    "cierre": "cierre_transparente",
    "timing": "lectura_contexto_timing",
    "perfil": "presentacion_perfil",
    "confianza": "valor_congruencia",
    "escucha": "comunicacion_escucha",
    "limites": "agencia_limites",
    "psicologia_femenina": "psicologia_femenina_preferencias",
}

PRINCIPLE_MARKERS = [
    "debe",
    "debes",
    "evita",
    "evitar",
    "conviene",
    "funciona",
    "clave",
    "importante",
    "regla",
    "recuerda",
    "cuando",
    "si ella",
    "no ",
    "mantén",
    "manten",
    "usa",
    "haz",
    "muestra",
    "genera",
]

RISK_TOKENS = [
    "manipul",
    "control",
    "hipnosis",
    "oscura",
    "dark",
    "dominar",
    "negar",
    "negging",
    "sumisa",
    "presion",
    "presión",
    "sexo",
    "sexual",
    "obedien",
]

STOPWORDS = {
    "para",
    "pero",
    "como",
    "cuando",
    "donde",
    "porque",
    "tambien",
    "también",
    "desde",
    "hasta",
    "este",
    "esta",
    "estos",
    "estas",
    "ellas",
    "ellos",
    "hacia",
    "sobre",
    "entre",
    "tiene",
    "tienes",
    "puede",
    "pueden",
    "hacer",
    "debe",
    "debes",
    "ser",
    "con",
    "los",
    "las",
    "una",
    "uno",
    "del",
    "que",
}


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\[EPUB_DOC:[^\]]+\]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-záéíóúñü0-9]{4,}", clean_text(text).lower())
        if token not in STOPWORDS
    }


def json_list(value: Any) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except Exception:
        return []
    if isinstance(data, list):
        return [str(item) for item in data if str(item).strip()]
    return []


def parse_concept_meta(value: Any) -> dict[str, list[str]]:
    try:
        data = json.loads(str(value or "{}"))
    except Exception:
        data = []
    if isinstance(data, dict):
        tags = data.get("tags") if isinstance(data.get("tags"), list) else []
        super_tags = data.get("super_tags") if isinstance(data.get("super_tags"), list) else []
        return {
            "tags": [str(item) for item in tags if str(item).strip()],
            "super_tags": [str(item) for item in super_tags if str(item).strip()],
        }
    if isinstance(data, list):
        return {
            "tags": [str(item) for item in data if str(item).strip()],
            "super_tags": [],
        }
    return {"tags": [], "super_tags": []}


def infer_tags(text: str) -> list[str]:
    lowered = clean_text(text).lower()
    tags = [
        tag
        for tag, patterns in TAG_PATTERNS.items()
        if any(pattern in lowered for pattern in patterns)
    ]
    return tags[:6]


def risk_level(text: str) -> tuple[str, str, str, str]:
    lowered = clean_text(text).lower()
    hits = [token for token in RISK_TOKENS if token in lowered]
    if any(token in lowered for token in ["manipul", "hipnosis", "oscura", "dark", "control"]):
        return ("high", "maximus_only_review", "silent_guarded", "explain_with_guardrails")
    if hits:
        return ("medium", "silent_strategy_guarded", "silent_strategy", "explain_with_context")
    return ("low", "silent_strategy", "silent_strategy", "explain_and_teach")


def infer_super_tags(tags: Iterable[str], risk: str) -> list[str]:
    result = [SUPER_TAG_MAP[tag] for tag in tags if tag in SUPER_TAG_MAP]
    if risk == "high":
        result.append("influencia_riesgo_manipulacion")
    if not result:
        result.append("fuente_teoria_vs_caso")
    return list(dict.fromkeys(result))[:5]


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    raw = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences: list[str] = []
    for sentence in raw:
        sentence = clean_text(sentence)
        if 60 <= len(sentence) <= 360:
            sentences.append(sentence)
    return sentences


def sentence_score(sentence: str, chunk_tags: Iterable[str]) -> int:
    lowered = sentence.lower()
    score = 0
    score += sum(2 for marker in PRINCIPLE_MARKERS if marker in lowered)
    score += len(set(infer_tags(sentence)) | set(chunk_tags))
    if "?" in sentence:
        score -= 1
    if any(bad in lowered for bad in ["copyright", "todos los derechos", "z-lib", "tabla de contenido"]):
        score -= 6
    return score


def normalize_principle(sentence: str) -> str:
    sentence = clean_text(sentence).strip(" -•|")
    sentence = re.sub(r"^[0-9]+[.)]\s*", "", sentence)
    if len(sentence) > 320:
        sentence = sentence[:317].rstrip() + "..."
    return sentence


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS book_principles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            chunk_id INTEGER NOT NULL,
            principle TEXT NOT NULL,
            category TEXT NOT NULL,
            concept_tags TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            voice_policy TEXT NOT NULL,
            natalia_use TEXT NOT NULL,
            maximus_use TEXT NOT NULL,
            source_reference TEXT,
            principle_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS principle_case_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            principle_id INTEGER NOT NULL,
            post_id TEXT NOT NULL,
            objective TEXT,
            link_score INTEGER NOT NULL,
            confidence TEXT NOT NULL,
            evidence_summary TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(principle_id, post_id)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_book_principles_category ON book_principles(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_book_principles_book ON book_principles(book_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_principle_links_post ON principle_case_links(post_id)")


def load_chunks(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT c.id AS chunk_id, c.book_id, c.chunk_index, c.texto, c.temas, c.tipo_contenido,
               c.capitulo, c.pagina_inicio, c.pagina_fin, c.section_title, c.page_estimate,
               b.slug, b.titulo, b.autor, b.categoria
        FROM chunks c
        JOIN books b ON b.id = c.book_id
        WHERE c.incluido_embedding = 1
          AND c.texto IS NOT NULL
          AND length(c.texto) > 160
          AND COALESCE(b.categoria, '') IN ('text_game', 'psicologia_femenina')
        ORDER BY c.book_id, c.chunk_index
        """
    ).fetchall()


def build_principles(conn: sqlite3.Connection, *, max_per_chunk: int) -> list[dict[str, Any]]:
    now = datetime.now().isoformat(timespec="seconds")
    rows = load_chunks(conn)
    principles: list[dict[str, Any]] = []
    for row in rows:
        chunk_tags = list(dict.fromkeys(json_list(row["temas"]) + infer_tags(row["texto"])))
        candidates = []
        for sentence in split_sentences(row["texto"]):
            score = sentence_score(sentence, chunk_tags)
            if score >= 2:
                candidates.append((score, sentence))
        candidates.sort(key=lambda item: item[0], reverse=True)
        for _, sentence in candidates[:max_per_chunk]:
            principle = normalize_principle(sentence)
            tags = list(dict.fromkeys(infer_tags(principle) + chunk_tags))[:6]
            if not tags:
                tags = ["general"]
            risk, voice_policy, natalia_use, maximus_use = risk_level(principle)
            super_tags = infer_super_tags(tags, risk)
            primary = super_tags[0]
            page = row["page_estimate"] or row["pagina_inicio"] or ""
            section = row["section_title"] or row["capitulo"] or ""
            source_reference = f"{row['titulo']} | {section or 'sin seccion'} | pag_estimada={page or 'n/d'} | chunk={row['chunk_index']}"
            digest = hashlib.sha1(f"{row['book_id']}|{row['chunk_id']}|{principle}".encode("utf-8")).hexdigest()[:16]
            principle_hash = f"{row['book_id']}:{row['chunk_id']}:{digest}"
            item = {
                "book_id": row["book_id"],
                "chunk_id": row["chunk_id"],
                "principle": principle,
                "category": primary,
                "concept_tags": json.dumps({"super_tags": super_tags, "tags": tags}, ensure_ascii=False),
                "risk_level": risk,
                "voice_policy": voice_policy,
                "natalia_use": natalia_use,
                "maximus_use": maximus_use,
                "source_reference": source_reference,
                "principle_hash": principle_hash,
                "created_at": now,
            }
            principles.append(item)
    conn.executemany(
        """
        INSERT OR IGNORE INTO book_principles (
            book_id, chunk_id, principle, category, concept_tags, risk_level, voice_policy,
            natalia_use, maximus_use, source_reference, principle_hash, created_at
        ) VALUES (
            :book_id, :chunk_id, :principle, :category, :concept_tags, :risk_level, :voice_policy,
            :natalia_use, :maximus_use, :source_reference, :principle_hash, :created_at
        )
        """,
        principles,
    )
    conn.commit()
    return principles


def load_success_cases() -> list[dict[str, Any]]:
    if not TEXTGAME_DB.exists():
        return []
    with sqlite3.connect(TEXTGAME_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT post_id, title_es, title, summary_es, translation_es, objectives_json,
                   score, source_url, subreddit
            FROM reddit_success_scrape_candidates
            WHERE status = 'candidate_qa'
              AND COALESCE(translation_es, '') != ''
            ORDER BY score DESC, updated_at DESC
            """
        ).fetchall()
    cases: list[dict[str, Any]] = []
    for row in rows:
        text = clean_text(" ".join(str(row[key] or "") for key in ["title_es", "title", "summary_es", "translation_es", "objectives_json"]))
        cases.append(
            {
                "post_id": str(row["post_id"]),
                "text": text,
                "tokens": tokens(text),
                "objectives": json_list(row["objectives_json"]),
                "score": int(row["score"] or 0),
                "summary": clean_text(row["summary_es"] or row["title_es"] or row["title"] or "")[:260],
                "url": row["source_url"],
            }
        )
    return cases


def objective_boost(tags: set[str], objectives: list[str], text: str) -> int:
    joined = " ".join(objectives).lower() + " " + text.lower()
    boost = 0
    if "cierre" in tags and any(word in joined for word in ["whatsapp", "numero", "número", "cita", "date", "instagram", "snapchat"]):
        boost += 3
    if "humor" in tags and any(word in joined for word in ["jaja", "haha", "humor", "risa", "gracioso"]):
        boost += 2
    if "opener" in tags and any(word in joined for word in ["abridor", "opener", "primer mensaje", "pickup"]):
        boost += 2
    if "timing" in tags and any(word in joined for word in ["15m", "1h", "hoy", "ayer", "respond"]):
        boost += 1
    return boost


def link_principles(conn: sqlite3.Connection, *, links_per_principle: int) -> int:
    cases = load_success_cases()
    if not cases:
        return 0
    conn.row_factory = sqlite3.Row
    principles = conn.execute(
        """
        SELECT id, principle, category, concept_tags, risk_level
        FROM book_principles
        ORDER BY id
        """
    ).fetchall()
    now = datetime.now().isoformat(timespec="seconds")
    links: list[dict[str, Any]] = []
    for principle in principles:
        concept_meta = parse_concept_meta(principle["concept_tags"])
        p_tokens = tokens(f"{principle['principle']} {principle['category']} {' '.join(concept_meta['tags'])} {' '.join(concept_meta['super_tags'])}")
        p_tags = set(concept_meta["tags"] + concept_meta["super_tags"] + [str(principle["category"])])
        scored: list[tuple[int, dict[str, Any]]] = []
        for case in cases:
            common = len(p_tokens & case["tokens"])
            if common <= 0:
                continue
            score = common + objective_boost(p_tags, case["objectives"], case["text"]) + min(case["score"], 10) // 4
            if score >= 4:
                scored.append((score, case))
        scored.sort(key=lambda item: item[0], reverse=True)
        for score, case in scored[:links_per_principle]:
            confidence = "alta" if score >= 8 else "media"
            links.append(
                {
                    "principle_id": principle["id"],
                    "post_id": case["post_id"],
                    "objective": ", ".join(case["objectives"][:4]),
                    "link_score": int(score),
                    "confidence": confidence,
                    "evidence_summary": case["summary"],
                    "created_at": now,
                }
            )
    conn.executemany(
        """
        INSERT OR IGNORE INTO principle_case_links (
            principle_id, post_id, objective, link_score, confidence, evidence_summary, created_at
        ) VALUES (
            :principle_id, :post_id, :objective, :link_score, :confidence, :evidence_summary, :created_at
        )
        """,
        links,
    )
    conn.commit()
    return len(links)


def table_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    conn.row_factory = sqlite3.Row
    total_principles = conn.execute("SELECT COUNT(*) FROM book_principles").fetchone()[0]
    total_links = conn.execute("SELECT COUNT(*) FROM principle_case_links").fetchone()[0]
    by_category = dict(conn.execute("SELECT category, COUNT(*) FROM book_principles GROUP BY category ORDER BY COUNT(*) DESC").fetchall())
    by_risk = dict(conn.execute("SELECT risk_level, COUNT(*) FROM book_principles GROUP BY risk_level ORDER BY COUNT(*) DESC").fetchall())
    linked = conn.execute("SELECT COUNT(DISTINCT principle_id) FROM principle_case_links").fetchone()[0]
    samples = [
        dict(row)
        for row in conn.execute(
            """
            SELECT p.category, p.risk_level, p.principle, p.source_reference,
                   l.post_id, l.objective, l.link_score, l.confidence, l.evidence_summary
            FROM book_principles p
            LEFT JOIN principle_case_links l ON l.principle_id = p.id
            ORDER BY l.link_score DESC, p.id
            LIMIT 25
            """
        )
    ]
    return {
        "book_principles": total_principles,
        "principle_case_links": total_links,
        "linked_principles": linked,
        "by_category": by_category,
        "by_risk": by_risk,
        "samples": samples,
    }


def write_html(summary: dict[str, Any], path: Path) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(item.get('category') or ''))}</td>"
        f"<td>{html.escape(str(item.get('risk_level') or ''))}</td>"
        f"<td>{html.escape(str(item.get('principle') or ''))}</td>"
        f"<td>{html.escape(str(item.get('objective') or ''))}</td>"
        f"<td>{html.escape(str(item.get('post_id') or ''))}</td>"
        f"<td>{html.escape(str(item.get('link_score') or ''))}</td>"
        f"<td>{html.escape(str(item.get('source_reference') or ''))}</td>"
        "</tr>"
        for item in summary["samples"]
    )
    categories = "".join(
        f"<li><strong>{html.escape(str(k))}</strong>: {int(v)}</li>"
        for k, v in summary["by_category"].items()
    )
    risks = "".join(
        f"<li><strong>{html.escape(str(k))}</strong>: {int(v)}</li>"
        for k, v in summary["by_risk"].items()
    )
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Principios Natalia: libros a casos reales</title>
<style>
body{{font-family:Arial,sans-serif;background:#0b0f17;color:#edf3ff;margin:0;padding:24px}}
section{{background:#121a26;border:1px solid #28364a;border-radius:8px;padding:18px;margin:16px 0}}
table{{width:100%;border-collapse:collapse;background:#090d14}}
th,td{{border:1px solid #263244;padding:8px;vertical-align:top}}
th{{background:#182235;color:#8cc8ff}} td{{color:#d8e3f6}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
</style>
</head>
<body>
<h1>Principios Natalia: libros -> casos reales</h1>
<p>Esta capa no reemplaza el RAG; agrega metadata auditable para que Natalia use teoria en silencio y Maximus pueda explicarla.</p>
<section class="grid">
<div><h2>Totales</h2><p>Principios: <strong>{summary['book_principles']}</strong></p><p>Enlaces a casos: <strong>{summary['principle_case_links']}</strong></p><p>Principios con caso real: <strong>{summary['linked_principles']}</strong></p></div>
<div><h2>Categorias</h2><ul>{categories}</ul></div>
<div><h2>Riesgo</h2><ul>{risks}</ul></div>
</section>
<section>
<h2>Muestras auditables</h2>
<table>
<thead><tr><th>Categoria</th><th>Riesgo</th><th>Principio</th><th>Objetivo caso</th><th>Post</th><th>Score link</th><th>Fuente libro</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</section>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-chunk", type=int, default=2)
    parser.add_argument("--links-per-principle", type=int, default=2)
    parser.add_argument("--append", action="store_true", help="No limpiar tablas generadas antes de reconstruir.")
    args = parser.parse_args()

    if not BOOKS_DB.exists():
        raise SystemExit(f"No existe {BOOKS_DB}")
    DOCS.mkdir(exist_ok=True)
    with sqlite3.connect(BOOKS_DB) as conn:
        ensure_schema(conn)
        if not args.append:
            conn.execute("DELETE FROM principle_case_links")
            conn.execute("DELETE FROM book_principles")
            conn.commit()
        built = build_principles(conn, max_per_chunk=max(1, args.max_per_chunk))
        links = link_principles(conn, links_per_principle=max(1, args.links_per_principle))
        summary = table_summary(conn)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary.update({"generated_at": stamp, "principles_built_this_run": len(built), "links_built_attempted_this_run": links})
    json_path = DOCS / f"book_principles_links_{stamp}.json"
    html_path = DOCS / f"book_principles_links_{stamp}.html"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(summary, html_path)
    print(json.dumps({"ok": True, "json": str(json_path), "html": str(html_path), **{k: summary[k] for k in ["book_principles", "principle_case_links", "linked_principles"]}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
