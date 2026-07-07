import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
LANGS = [
    ("en", "global_app_exact"),
    ("es", "multilang_global"),
    ("pt", "multilang_global"),
    ("fr", "multilang_global"),
    ("de", "multilang_global"),
    ("it", "multilang_global"),
]


def main() -> int:
    DOCS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        "event": "multilang_probe_start",
        "started_at": stamp,
        "max_requests_per_language": 300,
        "languages": [],
    }
    summary_path = DOCS / f"reddit_multilang_probe_{stamp}.json"

    for lang, profile in LANGS:
        run_label = f"probe_{lang}_{stamp}"
        stdout_path = DOCS / f"reddit_multilang_probe_{lang}_{stamp}.stdout.log"
        stderr_path = DOCS / f"reddit_multilang_probe_{lang}_{stamp}.stderr.log"
        cmd = [
            sys.executable,
            "scratch/reddit_success_parallel_pipeline.py",
            "--limit",
            "5000",
            "--max-requests",
            "300",
            "--run-label",
            run_label,
            "--query-profile",
            profile,
            "--language-probe",
            lang,
            "--workers",
            "6",
            "--batch-size",
            "6",
            "--discovery-workers",
            "8",
            "--decodo-rps",
            "6",
            "--discovery-window",
            "32",
            "--max-images-per-post",
            "2",
            "--min-reddit-score",
            "0",
            "--min-score",
            "8",
            "--min-ocr-lines",
            "4",
            "--defer-translation",
            "--progress-every",
            "10",
        ]
        item = {
            "language": lang,
            "query_profile": profile,
            "run_label": run_label,
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        with stdout_path.open("w", encoding="utf-8", errors="replace") as out, stderr_path.open(
            "w", encoding="utf-8", errors="replace"
        ) as err:
            proc = subprocess.run(
                cmd,
                cwd=ROOT,
                stdout=out,
                stderr=err,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        item["finished_at"] = datetime.now().isoformat(timespec="seconds")
        item["returncode"] = proc.returncode
        item["ok"] = proc.returncode == 0
        summary["languages"].append(item)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        if proc.returncode != 0:
            break

    summary["finished_at"] = datetime.now().isoformat(timespec="seconds")
    summary["ok"] = all(item.get("ok") for item in summary["languages"]) and len(summary["languages"]) == len(LANGS)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "summary": str(summary_path)}, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
