import os
import json
import logging
import sqlite3
import random
import time
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import GenericProxyConfig

# Configuración de Logs con aviso de error llamativo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scratch/retry_scraper_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

load_dotenv()

def get_clean_proxy_config():
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    user = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    
    if not host or not port or not user or not password:
        return None
        
    # En puerto 823 de DataImpulse, la IP rota automáticamente en cada petición.
    # Usamos las credenciales limpias sin sufijos inválidos.
    proxy_url = f"http://{user}:{password}@{host}:{port}"
    return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

def main():
    logging.info("♻️ Iniciando reintento de videos fallidos con proxies y headers de simulación...")
    
    db_path = 'textgame.db'
    if not os.path.exists(db_path):
        logging.error("❌ No existe la base de datos textgame.db")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener los videos que están en estado 'error'
    cursor.execute("SELECT video_id FROM transcripts WHERE status = 'error'")
    failed_videos = [row[0] for row in cursor.fetchall()]
    
    if not failed_videos:
        logging.info("✅ No hay videos en estado 'error' que requieran reintento.")
        conn.close()
        return
        
    logging.info(f"📋 Se encontraron {len(failed_videos)} videos fallidos para reintentar: {failed_videos}")
    
    # Cabeceras de simulación de navegador real
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for vid in failed_videos:
        # Delay aleatorio humano (5 a 12 segundos)
        delay = random.uniform(5, 12)
        logging.info(f"⏳ Esperando {delay:.2f} segundos para simular comportamiento humano...")
        time.sleep(delay)
        
        logging.info(f"🔎 Intentando descargar: {vid}")
        status = "error"
        raw_text = None
        message = ""
        
        try:
            # Crear sesión HTTP inyectando cabeceras personalizadas y proxy
            session = requests.Session()
            session.headers.update(browser_headers)
            
            proxy_config = get_clean_proxy_config()
            
            # YouTubeTranscriptApi permite pasar un objeto requests.Session() personalizado
            api = YouTubeTranscriptApi(proxy_config=proxy_config)
            
            # Realizar petición
            fetched_transcript = api.fetch(vid, languages=['es', 'en'])
            raw_data = fetched_transcript.to_raw_data()
            raw_text = " ".join([t['text'] for t in raw_data])
            status = "success"
            logging.info(f"✅ Éxito al descargar video {vid}")
            
        except TranscriptsDisabled:
            status = "disabled"
            logging.warning(f"⚠️ {vid} - Subtítulos desactivados por el creador.")
        except NoTranscriptFound:
            status = "not_found"
            logging.warning(f"⚠️ {vid} - No se encontraron subtítulos en los idiomas solicitados.")
        except Exception as e:
            status = "error"
            message = str(e)
            # ALERTA DE ERROR VISIBLE E INMEDIATA
            logging.error(f"🚨 ALERTA: Falló la descarga de {vid}. Razón: {message}")
            
        # Actualizar la base de datos
        cursor.execute('''
            UPDATE transcripts 
            SET status = ?, raw_text = ?, message = ?
            WHERE video_id = ?
        ''', (status, raw_text, message, vid))
        conn.commit()
        
    conn.close()
    logging.info("🏁 Proceso de reintento finalizado.")

if __name__ == "__main__":
    main()
