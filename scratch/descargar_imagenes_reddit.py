import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "textgame.db"
OUT_ROOT = ROOT / "imagenes"
DOCS_DIR = ROOT / "docs"
MANIFEST_PATH = DOCS_DIR / "imagenes_reddit_manifest.json"
CHUNK_SIZE = 1024 * 256


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def build_proxy():
    load_dotenv(ROOT / ".env")
    host = os.getenv("DATAIMPULSE_PROXY_HOST") or os.getenv("PROXY_HOST")
    port = os.getenv("DATAIMPULSE_PROXY_PORT") or os.getenv("PROXY_PORT")
    username = os.getenv("DATAIMPULSE_PROXY_USERNAME") or os.getenv("PROXY_USERNAME")
    password = os.getenv("DATAIMPULSE_PROXY_PASSWORD") or os.getenv("PROXY_PASSWORD")
    if not all([host, port, username, password]):
        raise RuntimeError("Faltan credenciales DataImpulse/PROXY en .env")

    session = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
    proxy = f"http://{username}_session-{session}:{password}@{host}:{port}"
    return {"http": proxy, "https": proxy}, f"{host}:{port}"


def image_extension(url):
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".jpg"


def imgur_thumbnail_url(url, suffix="l"):
    parsed = urlparse(url)
    if "i.imgur.com" not in parsed.netloc.lower():
        return url
    path = Path(parsed.path)
    stem = path.stem
    ext = path.suffix or ".jpg"
    if stem.endswith(("s", "b", "t", "m", "l", "h")):
        return url
    return f"{parsed.scheme}://{parsed.netloc}{path.parent.as_posix()}/{stem}{suffix}{ext}"


def image_jobs(limit=0):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        select id, post_id, image_urls
        from reddit_conversations
        where image_urls is not null and image_urls != '' and image_urls != '[]'
        order by id
        """
    ).fetchall()

    emitted = 0
    for row in rows:
        urls = json.loads(row["image_urls"] or "[]")
        for index, url in enumerate(urls, start=1):
            yield {
                "db_id": row["id"],
                "post_id": row["post_id"],
                "image_index": index,
                "url": url,
            }
            emitted += 1
            if limit and emitted >= limit:
                con.close()
                return
    con.close()


def target_path(job, out_root):
    name = f"img_{job['image_index']:03d}{image_extension(job['url'])}"
    return out_root / f"post_{job['post_id']}" / name


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(path):
    if not path.exists() or path.stat().st_size <= 0:
        return False, "", "", "", "archivo inexistente o vacio"
    try:
        with Image.open(path) as img:
            width, height = img.size
            image_format = img.format or ""
            img.verify()
        return True, width, height, image_format, ""
    except Exception as exc:
        return False, "", "", "", repr(exc)[:300]


def load_manifest(path):
    if not path.exists():
        return {"urls": {}, "hashes": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("urls", {})
        data.setdefault("hashes", {})
        return data
    except json.JSONDecodeError:
        return {"urls": {}, "hashes": {}}


def save_manifest(path, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def manifest_record(url, target, size, digest, width, height, fmt, source):
    return {
        "url": url,
        "target": target.relative_to(ROOT).as_posix(),
        "bytes": size,
        "sha256": digest,
        "width": width,
        "height": height,
        "format": fmt,
        "source": source,
        "updated_utc": now_utc(),
    }


def existing_from_manifest(manifest, url):
    record = manifest.get("urls", {}).get(url)
    if not record:
        return None
    target = ROOT / record.get("target", "")
    ok, width, height, fmt, _ = inspect_image(target)
    if not ok:
        return None
    return record, target, width, height, fmt


def ensure_report(report_path):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        return
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(
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
                "sha256",
                "width",
                "height",
                "format",
                "source",
                "proxy_estimated_mb",
                "error",
            ]
        )


def append_report(report_path, row):
    with report_path.open("a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(row)


def copy_verified(source_path, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != target.resolve():
        shutil.copy2(source_path, target)
    ok, width, height, fmt, error = inspect_image(target)
    if not ok:
        return None, error
    size = target.stat().st_size
    return (size, sha256_file(target), width, height, fmt), ""


def stream_download(session, url, target, headers, proxies, timeout, max_bytes):
    temp = target.with_suffix(target.suffix + ".part")
    if temp.exists():
        temp.unlink()

    with session.get(url, headers=headers, proxies=proxies, timeout=timeout, stream=True) as response:
        status_code = response.status_code
        if status_code != 200:
            return "failed_http", status_code, 0, "", "", "", "", f"http_status={status_code}"

        content_type = response.headers.get("content-type", "")
        if "image" not in content_type.lower():
            return "failed_not_image", status_code, 0, "", "", "", "", f"content-type={content_type}"

        content_length = response.headers.get("content-length")
        if content_length and max_bytes and int(content_length) > max_bytes:
            return "failed_too_large", status_code, 0, "", "", "", "", f"content-length={content_length}"

        bytes_written = 0
        with temp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if max_bytes and bytes_written > max_bytes:
                    temp.unlink(missing_ok=True)
                    return "failed_too_large", status_code, bytes_written, "", "", "", "", f"max_bytes={max_bytes}"
                handle.write(chunk)

    ok, width, height, fmt, error = inspect_image(temp)
    if not ok:
        temp.unlink(missing_ok=True)
        return "failed_invalid_image", status_code, bytes_written, "", "", "", "", error

    digest = sha256_file(temp)
    os.replace(temp, target)
    if not target.exists() or target.stat().st_size != bytes_written:
        return "failed_write_verify", status_code, bytes_written, digest, width, height, fmt, "archivo final no coincide"

    return "downloaded_verified", status_code, bytes_written, digest, width, height, fmt, ""


def download_one(session, proxies, manifest, job, out_root, timeout, direct_first, max_mb, prefer_imgur_thumbnail):
    target = target_path(job, out_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    original_url = job["url"]
    download_url = imgur_thumbnail_url(original_url) if prefer_imgur_thumbnail else original_url
    max_bytes = int(max_mb * 1024 * 1024) if max_mb else 0

    if target.exists() and target.stat().st_size > 0:
        ok, width, height, fmt, error = inspect_image(target)
        if ok:
            size = target.stat().st_size
            digest = sha256_file(target)
            manifest["urls"][original_url] = manifest_record(original_url, target, size, digest, width, height, fmt, "local_existing")
            manifest["hashes"][digest] = manifest["urls"][original_url]
            return "skipped_existing_verified", "", size, digest, width, height, fmt, "local_existing", ""

    existing = existing_from_manifest(manifest, original_url)
    if existing:
        record, source_path, width, height, fmt = existing
        copied, error = copy_verified(source_path, target)
        if copied:
            size, digest, width, height, fmt = copied
            manifest["urls"][original_url] = manifest_record(original_url, target, size, digest, width, height, fmt, "manifest_copy")
            manifest["hashes"][digest] = manifest["urls"][original_url]
            return "copied_from_manifest", "", size, digest, width, height, fmt, "manifest_copy", ""
        return "failed_manifest_copy", "", 0, "", "", "", "", "manifest_copy", error

    temp = target.with_suffix(target.suffix + ".part")
    if temp.exists():
        temp.unlink()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "Referer": "https://www.reddit.com/",
    }

    attempts = []
    if direct_first:
        attempts.append(("direct", None))
    attempts.append(("proxy", proxies))

    last_result = None
    for source, source_proxies in attempts:
        result = stream_download(session, download_url, target, headers, source_proxies, timeout, max_bytes)
        status, http_status, size, digest, width, height, fmt, error = result
        last_result = result + (source,)
        if status == "downloaded_verified":
            manifest["urls"][original_url] = manifest_record(original_url, target, size, digest, width, height, fmt, source)
            manifest["hashes"][digest] = manifest["urls"][original_url]
            return status, http_status, size, digest, width, height, fmt, source, ""
        if status in {"failed_not_image", "failed_too_large"}:
            break

    status, http_status, size, digest, width, height, fmt, error, source = last_result
    return status, http_status, size, digest, width, height, fmt, source, error


def write_summary(summary_path, report_path, out_root, expected_total):
    rows = list(csv.DictReader(report_path.open(encoding="utf-8"))) if report_path.exists() else []
    counts = {}
    total_downloaded_bytes = 0
    total_proxy_mb = 0.0
    direct_mb = 0.0
    missing = 0
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        if row["status"] == "downloaded_verified":
            try:
                total_downloaded_bytes += int(row["bytes"] or 0)
            except ValueError:
                pass
        try:
            row_mb = float(row["proxy_estimated_mb"] or 0)
            total_proxy_mb += row_mb
            if row.get("source") == "direct":
                direct_mb += int(row["bytes"] or 0) / 1024 / 1024
        except ValueError:
            pass
        if not (ROOT / row["target"]).exists():
            missing += 1

    physical = [p for p in out_root.rglob("*") if p.is_file() and not p.name.endswith(".part")] if out_root.exists() else []
    lines = [
        "# Descarga de imagenes Reddit",
        "",
        f"Actualizado UTC: {now_utc()}",
        f"Total esperado DB: {expected_total}",
        f"Filas CSV: {len(rows)}",
        f"Archivos fisicos: {len(physical)}",
        f"Targets CSV faltantes: {missing}",
        f"Bytes nuevos descargados/validados: {total_downloaded_bytes}",
        f"Consumo proxy estimado solo por cuerpos de imagen nuevos: {total_proxy_mb:.3f} MB",
        f"MB ahorrados estimados por descarga directa: {direct_mb:.3f} MB",
        "",
        "| Estado | Cantidad |",
        "|---|---:|",
    ]
    for status in sorted(counts):
        lines.append(f"| {status} | {counts[status]} |")
    lines.extend(["", f"Carpeta: `{out_root}`", f"CSV: `{report_path}`"])
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Descarga verificable de imagenes Reddit a la carpeta imagenes.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay-min", type=float, default=8.0)
    parser.add_argument("--delay-max", type=float, default=15.0)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--proxy-only", action="store_true", help="No intenta descarga directa; usa siempre proxy.")
    parser.add_argument("--max-mb", type=float, default=12.0, help="Tamano maximo por imagen antes de cortar.")
    parser.add_argument(
        "--prefer-imgur-thumbnail",
        action="store_true",
        help="Usa thumbnails livianos de i.imgur.com. Ahorra proxy, pero puede degradar OCR.",
    )
    parser.add_argument("--manifest-path", default=str(MANIFEST_PATH))
    parser.add_argument("--output-root", default=str(OUT_ROOT))
    parser.add_argument("--report-path", default="")
    parser.add_argument("--summary-path", default="")
    args = parser.parse_args()

    out_root = Path(args.output_root).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(args.report_path).resolve() if args.report_path else DOCS_DIR / f"imagenes_reddit_{stamp}.csv"
    summary_path = Path(args.summary_path).resolve() if args.summary_path else DOCS_DIR / f"imagenes_reddit_{stamp}_summary.md"
    manifest_path = Path(args.manifest_path).resolve()

    jobs = list(image_jobs(args.limit))
    expected_total = len(list(image_jobs(0)))
    ensure_report(report_path)
    manifest = load_manifest(manifest_path)
    proxies, proxy_label = build_proxy()
    session = requests.Session()

    print(f"Inicio UTC={now_utc()} proxy={proxy_label} destino={out_root}", flush=True)
    print(f"Imagenes de esta corrida={len(jobs)} total_db={expected_total}", flush=True)

    for position, job in enumerate(jobs, start=1):
        status = "failed_exception"
        http_status = ""
        size = 0
        digest = ""
        width = ""
        height = ""
        fmt = ""
        download_source = "unknown"
        error = ""

        for attempt in range(1, args.retries + 2):
            try:
                status, http_status, size, digest, width, height, fmt, download_source, error = download_one(
                    session,
                    proxies,
                    manifest,
                    job,
                    out_root,
                    args.timeout,
                    not args.proxy_only,
                    args.max_mb,
                    args.prefer_imgur_thumbnail,
                )
                if status in {"downloaded_verified", "skipped_existing_verified", "copied_from_manifest"}:
                    break
            except Exception as exc:
                error = repr(exc)[:300]
                status = "failed_exception"
            if attempt <= args.retries:
                time.sleep(random.uniform(args.delay_min, args.delay_max))

        target = target_path(job, out_root)
        source = "unknown"
        if status in {"skipped_existing_verified", "copied_from_manifest"}:
            source = "local"
        elif status == "downloaded_verified":
            source = download_source
        proxy_mb = size / 1024 / 1024 if status == "downloaded_verified" and source == "proxy" else 0
        append_report(
            report_path,
            [
                now_utc(),
                job["db_id"],
                job["post_id"],
                job["image_index"],
                job["url"],
                target.relative_to(ROOT).as_posix(),
                status,
                http_status,
                size,
                digest,
                width,
                height,
                fmt,
                source,
                f"{proxy_mb:.6f}",
                error,
            ],
        )
        save_manifest(manifest_path, manifest)
        write_summary(summary_path, report_path, out_root, expected_total)
        print(f"[{position}/{len(jobs)}] {job['post_id']} img_{job['image_index']}: {status} {size} bytes", flush=True)

        if position < len(jobs):
            time.sleep(random.uniform(args.delay_min, args.delay_max))

    write_summary(summary_path, report_path, out_root, expected_total)
    save_manifest(manifest_path, manifest)
    print(f"Fin UTC={now_utc()} resumen={summary_path}", flush=True)


if __name__ == "__main__":
    main()
