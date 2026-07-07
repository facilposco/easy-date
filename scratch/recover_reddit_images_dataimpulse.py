import argparse
import csv
import json
import os
import random
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
OUT_ROOT = ROOT / "downloaded_files"
DOCS_DIR = ROOT / "docs"
REPORT_PATH = DOCS_DIR / "reddit_image_recovery_dataimpulse.csv"
SUMMARY_PATH = DOCS_DIR / "reddit_image_recovery_dataimpulse_summary.md"


def proxy_from_env():
    load_dotenv(ROOT / ".env")
    host = os.getenv("DATAIMPULSE_PROXY_HOST") or os.getenv("PROXY_HOST")
    port = os.getenv("DATAIMPULSE_PROXY_PORT") or os.getenv("PROXY_PORT")
    user = os.getenv("DATAIMPULSE_PROXY_USERNAME") or os.getenv("PROXY_USERNAME")
    password = os.getenv("DATAIMPULSE_PROXY_PASSWORD") or os.getenv("PROXY_PASSWORD")
    if not all([host, port, user, password]):
        raise RuntimeError("Faltan credenciales DataImpulse/PROXY en .env")
    session_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
    user_with_session = f"{user}_session-{session_id}"
    proxy_url = f"http://{user_with_session}:{password}@{host}:{port}"
    return {"http": proxy_url, "https": proxy_url}, f"{host}:{port}", user_with_session


def extension_from_url(url):
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".jpg"


def iter_image_jobs(limit=None, out_root=OUT_ROOT, prefer_db_local_paths=True):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        select id, post_id, image_urls, local_image_paths
        from reddit_conversations
        where image_urls is not null and image_urls != '' and image_urls != '[]'
        order by id
        """
    ).fetchall()
    emitted = 0
    for row in rows:
        urls = json.loads(row["image_urls"] or "[]")
        local_paths = json.loads(row["local_image_paths"] or "[]")
        for index, url in enumerate(urls, start=1):
            if prefer_db_local_paths and index - 1 < len(local_paths) and local_paths[index - 1]:
                target = ROOT / local_paths[index - 1]
            else:
                target = out_root / f"post_{row['post_id']}" / f"img_{index}{extension_from_url(url)}"
            yield {
                "db_id": row["id"],
                "post_id": row["post_id"],
                "index": index,
                "url": url,
                "target": target,
            }
            emitted += 1
            if limit and emitted >= limit:
                return


def write_report_header_if_needed(report_path):
    report_path.parent.mkdir(exist_ok=True)
    if report_path.exists():
        return
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp_utc",
                "db_id",
                "post_id",
                "image_index",
                "url",
                "target",
                "status",
                "http_status",
                "bytes",
                "error",
            ]
        )


def append_report(report_path, row):
    with report_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def download_one(session, job, proxies, timeout):
    target = job["target"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return "skipped_existing", "", target.stat().st_size, ""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.reddit.com/",
    }
    response = session.get(job["url"], headers=headers, proxies=proxies, timeout=timeout)
    http_status = response.status_code
    if response.status_code != 200:
        return "failed_http", http_status, 0, response.text[:300]
    target.write_bytes(response.content)
    return "downloaded", http_status, len(response.content), ""


def summarize(started_at, total_jobs, stats, proxy_label, delay_min, delay_max, report_path, summary_path, out_root):
    lines = [
        "# Recuperacion de imagenes Reddit con DataImpulse",
        "",
        f"Inicio UTC: {started_at}",
        f"Fin UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Proxy: {proxy_label}",
        f"Intervalo entre descargas: {delay_min}-{delay_max} segundos",
        f"Total jobs: {total_jobs}",
        "",
        "| Estado | Cantidad |",
        "|---|---:|",
    ]
    for key in sorted(stats):
        lines.append(f"| {key} | {stats[key]} |")
    lines.extend(
        [
            "",
            f"CSV detallado: `{report_path.relative_to(ROOT).as_posix()}`",
            f"Carpeta destino: `{out_root.relative_to(ROOT).as_posix()}`",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Recupera imagenes Reddit via DataImpulse.")
    parser.add_argument("--limit", type=int, default=0, help="Limite opcional de imagenes.")
    parser.add_argument("--delay-min", type=float, default=5.0)
    parser.add_argument("--delay-max", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--output-root", default=str(OUT_ROOT), help="Carpeta destino de imagenes.")
    parser.add_argument("--report-path", default=str(REPORT_PATH), help="CSV de reporte.")
    parser.add_argument("--summary-path", default=str(SUMMARY_PATH), help="Resumen markdown.")
    parser.add_argument(
        "--ignore-db-local-paths",
        action="store_true",
        help="Fuerza output-root aunque la DB tenga local_image_paths historicos.",
    )
    args = parser.parse_args()

    out_root = Path(args.output_root).resolve()
    report_path = Path(args.report_path).resolve()
    summary_path = Path(args.summary_path).resolve()
    proxies, proxy_label, proxy_user = proxy_from_env()
    jobs = list(
        iter_image_jobs(
            limit=args.limit or None,
            out_root=out_root,
            prefer_db_local_paths=not args.ignore_db_local_paths,
        )
    )
    write_report_header_if_needed(report_path)
    started_at = datetime.now(timezone.utc).isoformat()
    stats = {}
    session = requests.Session()

    print(f"Agente DataImpulse iniciado. Proxy={proxy_label} usuario_sesion=redactado")
    print(f"Imagenes objetivo: {len(jobs)}. Destino: {out_root}")

    for position, job in enumerate(jobs, start=1):
        status = "failed"
        http_status = ""
        size = 0
        error = ""
        for attempt in range(1, args.retries + 2):
            try:
                status, http_status, size, error = download_one(session, job, proxies, args.timeout)
                if status in {"downloaded", "skipped_existing"}:
                    break
            except Exception as exc:
                error = repr(exc)[:300]
                status = "failed_exception"
            if attempt <= args.retries:
                time.sleep(random.uniform(args.delay_min, args.delay_max))

        stats[status] = stats.get(status, 0) + 1
        append_report(
            report_path,
            [
                datetime.now(timezone.utc).isoformat(),
                job["db_id"],
                job["post_id"],
                job["index"],
                job["url"],
                job["target"].relative_to(ROOT).as_posix(),
                status,
                http_status,
                size,
                error,
            ]
        )
        print(f"[{position}/{len(jobs)}] {job['post_id']} img_{job['index']}: {status} {size} bytes")

        if position < len(jobs):
            time.sleep(random.uniform(args.delay_min, args.delay_max))

    summarize(started_at, len(jobs), stats, proxy_label, args.delay_min, args.delay_max, report_path, summary_path, out_root)
    print(f"Resumen: {summary_path}")


if __name__ == "__main__":
    main()
