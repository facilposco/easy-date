import os
import json
import logging
import sqlite3
import random
import time
import requests
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv

# Parchear requests.Session para emular el TLS Fingerprint de Chrome 110 y evitar WAFs
class PatchedSession(curl_requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs['impersonate'] = 'chrome110'
        super().__init__(*args, **kwargs)

requests.Session = PatchedSession

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import GenericProxyConfig


# Configuración de Logs (Trazabilidad Obligatoria)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno seguro (.env)
load_dotenv()

def get_proxy_config():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    
    if not host or not port or not user or not password:
        logging.warning("⚠️ No se detectó proxy completo en el archivo .env. Ejecutando sin proxy (Riesgo de bloqueo).")
        return None
        
    proxy_url = f"http://{user}:{password}@{host}:{port}"
    return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

def extract_id(line):
    if "v=" in line:
        return line.split("v=")[1].split("&")[0].strip()
    elif "youtu.be/" in line:
        return line.split("youtu.be/")[1].split("?")[0].strip()
    return line.strip()

def read_video_ids(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line for line in f if line.strip() and not line.startswith('#')]
            ids = [extract_id(line) for line in lines]
            # Eliminar duplicados manteniendo orden
            return list(dict.fromkeys(ids))
    except FileNotFoundError:
        logging.error(f"❌ No se encontró el archivo {filepath}.")
        return []

def main():
    logging.info("🚀 Iniciando extracción masiva de YouTube Captions...")
    proxy_config = get_proxy_config()
    api = YouTubeTranscriptApi(proxy_config=proxy_config)
    
    video_ids = read_video_ids("videos.txt")
    if not video_ids:
        logging.error("❌ Lista de videos vacía. Añade IDs a videos.txt")
        return

    results = []
    
    for vid in video_ids:
        logging.info(f"🔎 Extrayendo ID: {vid}")
        try:
            fetched_transcript = api.fetch(vid, languages=['es', 'en'])
            raw_data = fetched_transcript.to_raw_data()
            
            full_text = " ".join([t['text'] for t in raw_data])
            results.append({
                "video_id": vid,
                "status": "success",
                "raw_text": full_text
            })
            logging.info(f"✅ Éxito extrayendo: {vid}")
            
        except TranscriptsDisabled:
            logging.error(f"❌ {vid} - Subtítulos desactivados por el creador.")
            results.append({"video_id": vid, "status": "disabled"})
        except NoTranscriptFound:
            logging.error(f"❌ {vid} - No se encontraron subtítulos en los idiomas solicitados.")
            results.append({"video_id": vid, "status": "not_found"})
        except Exception as e:
            logging.error(f"❌ {vid} - Error crítico: {str(e)}")
            results.append({"video_id": vid, "status": "error", "message": str(e)})

    # Guardar base de datos cruda en SQLite (Cero Alucinaciones y Base Futura)
    db_path = 'textgame.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcripts (
            video_id TEXT PRIMARY KEY,
            status TEXT,
            raw_text TEXT,
            message TEXT
        )
    ''')
    
    for r in results:
        cursor.execute('''
            INSERT OR REPLACE INTO transcripts (video_id, status, raw_text, message)
            VALUES (?, ?, ?, ?)
        ''', (r.get('video_id'), r.get('status'), r.get('raw_text'), r.get('message', '')))
    
    conn.commit()
    conn.close()
        
    logging.info(f"📁 Proceso finalizado. Datos guardados en la base de datos SQLite: {db_path}")

if __name__ == "__main__":
    main()
