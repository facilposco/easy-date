import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"


def run_step(name: str, args: list[str]) -> dict:
    started = datetime.now().isoformat(timespec="seconds")
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "name": name,
        "started_at": started,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2500:],
        "stderr_tail": proc.stderr[-2500:],
        "ok": proc.returncode == 0,
    }


def main() -> int:
    DOCS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    index_report = DOCS_DIR / f"natalia_rag_daily_index_{stamp}.json"
    graph_report = DOCS_DIR / f"natalia_objective_graph_daily_{stamp}.json"
    steps = [
        run_step(
            "translate_pending_success",
            ["scratch/translate_reddit_success_candidates.py", "--limit", "100", "--provider", "google"],
        ),
        run_step(
            "index_incremental_success_and_negatives",
            [
                "scratch/index_success_candidates_chroma.py",
                "--incremental",
                "--batch-size",
                "100",
                "--index-negatives",
                "--negative-limit",
                "1000",
                "--report",
                str(index_report),
            ],
        ),
        run_step("sync_success_chroma_deletes_dry_run", ["scratch/sync_success_chroma_deletes.py"]),
        run_step(
            "build_book_principles_and_links",
            ["scratch/build_book_principles_and_links.py", "--max-per-chunk", "2", "--links-per-principle", "2"],
        ),
        run_step("build_objective_graph", ["scratch/build_natalia_objective_graph.py"]),
        run_step("qa_20", ["scratch/qa_natalia_rag_20.py"]),
        run_step("generate_eval_catalog", ["scratch/generate_natalia_rag_eval_catalog.py"]),
        run_step("qa_eval_catalog", ["scratch/qa_natalia_rag_catalog.py"]),
    ]
    summary = {
        "generated_at": stamp,
        "ok": all(step["ok"] for step in steps),
        "steps": steps,
        "index_report": str(index_report),
        "objective_graph_report_hint": str(graph_report),
    }
    out = DOCS_DIR / f"natalia_rag_daily_maintenance_{stamp}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "report": str(out)}, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
