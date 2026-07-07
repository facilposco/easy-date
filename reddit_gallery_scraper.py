import os
import json
import time
import random
from curl_cffi import requests
from dotenv import load_dotenv

# Cargar Proxy
load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
proxy_url = f"http://{user}:{password}@{host}:{port}"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

print("Iniciando escaneo de r/Tinder para galerías (carruseles)...")
print(f"Proxy configurado: {host}:{port}")

try:
    print("Aplicando regla de intervalo de tiempo (sleep aleatorio 5-10s)...")
    time.sleep(random.uniform(5, 10))
    
    print("Obteniendo top posts...")
    res = requests.get('https://www.reddit.com/r/Tinder/top.json?limit=100&t=all', 
                       headers=headers, 
                       impersonate='chrome110', 
                       proxies=proxies, 
                       timeout=20)
                       
    print(f"HTTP Status: {res.status_code}")
    
    if res.status_code == 200:
        data = res.json()
        posts = data['data']['children']
        galleries = [p['data'] for p in posts if 'gallery_data' in p['data']]
        
        print(f"¡Éxito! Encontrados {len(galleries)} posts de tipo galería.")
    else:
        print(f"ERROR FATAL: El WAF de Reddit bloqueó la conexión (HTTP {res.status_code}).")
        print(res.text[:500])
        
except Exception as e:
    print(f"Error de conexión: {e}")
