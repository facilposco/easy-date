import sys
import os
import random
from dotenv import load_dotenv

# Añadir la ruta local de yars al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scratch', 'yars', 'src')))

try:
    from yars.yars import YARS
except ImportError as e:
    print(f"Error importando YARS: {e}")
    sys.exit(1)

# Cargar proxy
load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

# El formato correcto para pasar a requests
proxy_url = f"http://{user}:{password}@{host}:{port}"

print("Inicializando YARS (Zero-Auth) con proxy residencial...")
# Instanciar YARS
miner = YARS(proxy=proxy_url, timeout=20, random_user_agent=True)

try:
    print("Probando extracción en r/Tinder (Top de la semana)...")
    # Intentamos obtener 10 posts
    posts = miner.fetch_subreddit_posts("Tinder", limit=10, category="top", time_filter="week")
    
    if posts:
        print(f"¡Éxito! YARS extrajo {len(posts)} posts:")
        for p in posts[:3]:
            print(f"- {p['title']}")
    else:
        print("No se extrajeron posts, es probable que haya sido bloqueado o la lista este vacía.")
except Exception as e:
    print(f"Error en tiempo de ejecución: {e}")
