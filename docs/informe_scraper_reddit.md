# Informe: Scraper de Reddit en Easy Date

Fecha: 2026-06-28

## Hallazgo principal

El proyecto si contiene desarrollo de scraper de Reddit. Hay dos lineas principales:

1. `reddit_bulk_scraper.py`: scraper masivo con Decodo Scraping API.
2. `reddit_sb_extractor.py` y variantes `reddit_sb_*`: pruebas con SeleniumBase/Undetected ChromeDriver y proxy residencial.

Para las 211 conversaciones con rutas `downloaded_files/post_<post_id>/img_N.jpg`, el archivo que mejor coincide con la estructura de la base de datos es `reddit_bulk_scraper.py`.

## Evidencia del scraper Decodo

Archivo: `reddit_bulk_scraper.py`

- Define `DECODO_URL = "https://scraper-api.decodo.com/v2/scrape"`.
- Consulta `https://www.reddit.com/r/Tinder/search.json`.
- Busca posts con query: `flair:success OR title:success OR title:date OR title:number OR title:whatsapp OR title:tinder`.
- Detecta galerias con `gallery_data` y `media_metadata`.
- Construye URLs originales `https://i.redd.it/<media_id>.<ext>`.
- Descarga imagenes a `downloaded_files/post_<post_id>/img_N.jpg`.
- Guarda en SQLite usando `db_manager.insert_conversation(...)`.

Este flujo coincide con las columnas de `textgame.db`:

- `image_urls`
- `local_image_paths`
- `post_type`
- `body_text`
- `created_utc`

## Evidencia de ejecucion

Archivo: `scraper_log.txt`

- Registra llamadas a Decodo.
- Registra paginas cargadas.
- Registra errores puntuales descargando imagenes desde `i.redd.it`.
- Registra totales historicos como carruseles, texto puro e imagen unica.

Archivo: `docs/usage_2026-06-20_2026-06-27.csv`

- Registra trafico proxy hacia `www.reddit.com`, `old.reddit.com`, `oauth.reddit.com` e `i.redd.it`.

## Arquitectura documentada

Archivo: `arquitectura.html`

- Documenta `reddit_sb_extractor.py` como extractor de Reddit.
- Documenta el uso de SeleniumBase UC, proxies residenciales y reglas anti-bloqueo.
- Documenta DataImpulse como proxy residencial.
- No menciona Decodo directamente en el estado actual del documento.

## Interpretacion

La documentacion arquitectonica quedo apuntando a la linea SeleniumBase/DataImpulse, pero el scraper que mejor explica la tabla SQLite y las rutas `downloaded_files` es `reddit_bulk_scraper.py` con Decodo Scraping API.

Probablemente hubo dos fases:

1. Pruebas de evasion con Playwright/SeleniumBase/DataImpulse.
2. Escaneo masivo funcional con Decodo Scraping API, guardando posts e imagenes en SQLite.

## Riesgos detectados

- Hay credenciales/API tokens embebidos en algunos scripts antiguos. Deben moverse a `.env` y rotarse.
- `reddit_bulk_scraper.py` descarga imagenes con `urllib.request` directo, sin proxy para `i.redd.it`; eso pudo causar errores y bloqueos.
- La carpeta `downloaded_files` fue borrada, aunque SQLite conserva las rutas y OCR.
- `arquitectura.html` debe actualizarse para reflejar Decodo si ese fue el flujo real.

## Recomendacion

Para reconstruir imagenes o hacer nuevos escaneos:

- Usar `.env` para credenciales.
- Descargar imagenes con proxy residencial o Decodo, no con `urllib` directo.
- Aplicar espera de 5 a 10 segundos entre descargas.
- Registrar log en `docs/`.
- No rehacer OCR si `transcription_json` ya existe.
- Guardar nuevamente en `downloaded_files/post_<post_id>/img_N.jpg` para que coincida con SQLite.
