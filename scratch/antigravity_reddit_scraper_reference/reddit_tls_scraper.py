import tls_client
import json
import os
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

proxy = f"http://{user}:{password}@{host}:{port}"

session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

proxies = {
    "http": proxy,
    "https": proxy
}

url = "https://www.reddit.com/r/Tinder/top.json?limit=10&t=week"
print(f"Navegando a: {url} con tls_client...")

try:
    response = session.get(
        url,
        proxy=proxy, # tls_client uses proxy= string directly in newer versions or proxies= dict
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    )
    
    print(f"Status HTTP: {response.status_code}")
    
    if response.status_code == 403:
        print("ERROR 403: El WAF bloqueo la conexion en tls_client.")
    else:
        try:
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            print(f"¡EXITO! WAF BYPASSED. Se extrajeron {len(posts)} posts.")
            with open("scratch/reddit_top_posts_tls.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Error parseando JSON (posible challenge html):")
            print(response.text[:500])
except Exception as e:
    print(f"Excepcion: {e}")
