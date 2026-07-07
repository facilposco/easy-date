import argparse
import csv
import html
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
sys.path.insert(0, str(ROOT_DIR))

from backend import server  # noqa: E402


SOURCE_MATCHERS = {
    "natalia_success_cases": {"success_chroma"},
    "natalia_negative_cases": {"negative_chroma"},
    "natalia_books_kb": {"books_chroma", "books_conversations_chroma"},
    "natalia_conversations": {"chroma"},
}


def normalize_profile(profile: str) -> str:
    if profile == "alta_selectividad":
        return "desinteresada"
    return profile or "coqueta"


def summarize_case(case: dict) -> str:
    text = server.clean_ui_text(case.get("text", ""))
    lines = [line for line in text.splitlines() if line.strip()]
    return " | ".join(lines[:2])[:260]


def retrieve_for_catalog(row: dict) -> list[dict]:
    question = row["pregunta"]
    profile = normalize_profile(row.get("perfil", "coqueta"))
    cases: list[dict] = []
    expected = set(row["colecciones_esperadas"].split("|"))
    if "natalia_success_cases" in expected:
        cases.extend(server.retrieve_success_chroma_cases(question, limit=3))
    if "natalia_negative_cases" in expected:
        cases.extend(server.retrieve_negative_chroma_cases(question, limit=2))
    if "natalia_books_kb" in expected:
        cases.extend(server.retrieve_books_chroma_cases(question, limit=2))
    if "natalia_conversations" in expected:
        cases.extend(server.retrieve_chroma_cases(question, profile, limit=2))
    return cases


def evaluate_row(row: dict) -> dict:
    cases = retrieve_for_catalog(row)
    sources = [str(case.get("source") or "") for case in cases]
    expected = [item for item in row["colecciones_esperadas"].split("|") if item]
    hits = []
    misses = []
    for collection in expected:
        allowed = SOURCE_MATCHERS.get(collection, {collection})
        if any(source in allowed for source in sources):
            hits.append(collection)
        else:
            misses.append(collection)

    first_case = cases[0] if cases else {}
    result = "OK" if not misses else "FALTA_EVIDENCIA"
    return {
        **row,
        "resultado": result,
        "colecciones_encontradas": "|".join(hits),
        "colecciones_faltantes": "|".join(misses),
        "fuentes_recuperadas": ", ".join(
            f"{case.get('source')}:{case.get('post_id')}" for case in cases[:8]
        ),
        "evidencia_muestra": summarize_case(first_case) if first_case else "",
        "casos_recuperados": len(cases),
    }


def load_catalog(path: Path, limit: int) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows[:limit] if limit else rows


def write_reports(rows: list[dict]) -> dict:
    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = DOCS_DIR / f"natalia_rag_eval_catalog_run_{stamp}.csv"
    json_path = DOCS_DIR / f"natalia_rag_eval_catalog_run_{stamp}.json"
    html_path = DOCS_DIR / f"natalia_rag_eval_catalog_run_{stamp}.html"
    summary = {
        "total": len(rows),
        "ok": sum(1 for row in rows if row["resultado"] == "OK"),
        "falta_evidencia": sum(1 for row in rows if row["resultado"] != "OK"),
    }
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    table = "\n".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in [
                "id",
                "categoria",
                "intencion",
                "perfil",
                "pregunta",
                "colecciones_esperadas",
                "colecciones_faltantes",
                "fuentes_recuperadas",
                "resultado",
            ]
        )
        + "</tr>"
        for row in rows
    )
    html_path.write_text(
        f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>QA catalogo RAG Natalia</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#10131a; color:#eef2ff; margin:24px; }}
    .ok {{ color:#43d17a; }}
    .bad {{ color:#ff6b6b; }}
    table {{ border-collapse:collapse; width:100%; font-size:12px; }}
    th, td {{ border:1px solid #2e3445; padding:8px; vertical-align:top; }}
    th {{ background:#1f2635; position:sticky; top:0; }}
    tr:nth-child(even) {{ background:#151b27; }}
  </style>
</head>
<body>
  <h1>QA catalogo RAG Natalia</h1>
  <p>Total: {summary['total']} | OK: <span class="ok">{summary['ok']}</span> | Falta evidencia: <span class="bad">{summary['falta_evidencia']}</span></p>
  <table>
    <thead><tr><th>ID</th><th>Categoria</th><th>Intencion</th><th>Perfil</th><th>Pregunta</th><th>Esperadas</th><th>Faltantes</th><th>Fuentes</th><th>Resultado</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return {"csv": str(csv_path), "json": str(json_path), "html": str(html_path), "summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=str(DOCS_DIR / "natalia_rag_eval_catalog_v1.csv"))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalogo no encontrado: {catalog_path}")
    rows = [evaluate_row(row) for row in load_catalog(catalog_path, args.limit)]
    paths = write_reports(rows)
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0 if paths["summary"]["falta_evidencia"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
