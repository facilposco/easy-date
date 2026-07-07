import requests
from curl_cffi import requests as curl_requests
import sys

# Forzar codificación de consola a UTF-8 para evitar errores de emojis en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Clonar clase para parchear requests.Session
class PatchedSession(curl_requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs['impersonate'] = 'chrome110'
        super().__init__(*args, **kwargs)

requests.Session = PatchedSession

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

print("Parche aplicado. Probando descarga de un video...")
try:
    # Probar con un video exitoso conocido sin proxy para verificar que curl-cffi funciona
    api = YouTubeTranscriptApi()
    transcript = api.fetch('0IUoTwkmRKs', languages=['es', 'en'])
    data = transcript.to_raw_data()
    print("¡Éxito! Descarga correcta usando el parche curl-cffi.")
    print("Primeros 100 caracteres:", " ".join([t['text'] for t in data[:3]]))
except Exception as e:
    print(f"Error: {e}")
