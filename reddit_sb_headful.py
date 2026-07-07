import os
import time
import random
import string
from dotenv import load_dotenv
from seleniumbase import Driver

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
proxy_user = f"{user}_session-{session_id}"
proxy_string = f"{proxy_user}:{password}@{host}:{port}"

print(f"Probando SeleniumBase UC en modo VISIBLE (headful=True)...")
print(f"Proxy User: {proxy_user}")

# Configurar driver con headless=False (modo visible)
driver = Driver(uc=True, headless=False, proxy=proxy_string)
try:
    url = "https://www.reddit.com/r/Tinder/top.json?limit=1"
    print(f"Navegando a: {url}")
    driver.uc_open_with_reconnect(url, 10)
    
    # Esperar a que el WAF/Cloudflare cargue (si sale reto, el usuario podría resolverlo o UC mode lo pasa solo)
    print("Esperando 15 segundos para resolución de página...")
    time.sleep(15)
    
    html = driver.page_source
    print(f"Tamaño de página recibida: {len(html)} bytes")
    print(f"Primeros 200 caracteres: {html[:200]}")
    
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/sb_headful_output.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    if "network security" in html.lower():
        print("Bloqueado por seguridad de red (WAF).")
    elif len(html) < 200:
        print("Página vacía (posible fallo de autenticación del proxy).")
    else:
        print("¡Respuesta exitosa! Data cargada en scratch/sb_headful_output.html")
        
except Exception as e:
    print("Ocurrió un error:", e)
finally:
    driver.quit()
