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
# Formato de sesion rotada para DataImpulse
proxy_user = f"{user}_session-{session_id}"
proxy_string = f"{proxy_user}:{password}@{host}:{port}"

print(f"Probando SeleniumBase UC con proxy rotado (Headless2)...")
print(f"Proxy User: {proxy_user}")

# Usar headless2=True que emula navegación headful de forma invisible
driver = Driver(uc=True, headless2=True, proxy=proxy_string)
try:
    url = "https://www.reddit.com/r/Tinder/top.json?limit=1"
    print(f"Abriendo: {url}")
    driver.uc_open_with_reconnect(url, 10)
    time.sleep(10)
    
    html = driver.page_source
    print(f"Tamaño de página recibida: {len(html)} bytes")
    print(f"Primeros 200 caracteres: {html[:200]}")
    
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/sb_headful_test.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    if "network security" in html.lower():
        print("Bloqueado por seguridad de red (WAF).")
    elif len(html) < 200:
        print("Página vacía (posible fallo de autenticación de proxy).")
    else:
        print("¡Respuesta recibida! Verificando si es JSON o HTML...")
        if "{" in html[:50]:
            print("Parece JSON válido.")
        else:
            print("Parece HTML normal.")
            
except Exception as e:
    print("Ocurrió un error:", e)
finally:
    driver.quit()
