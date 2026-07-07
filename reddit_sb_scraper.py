import os
import json
import time
import random
from dotenv import load_dotenv
from seleniumbase import Driver

# Cargar proxy
load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

# SeleniumBase usa formato host:port y luego autenticacion separada si se requiere, 
# pero la version mas facil para proxies con auth en UC mode es usar una extension proxy.
# Afortunadamente SeleniumBase soporta proxy='user:pass@host:port'
proxy_string = f"{user}:{password}@{host}:{port}"

print("Iniciando Chrome en Modo UC (Undetected ChromeDriver)...")
driver = None
try:
    # UC mode = Undetected ChromeDriver (bypass Cloudflare)
    # headless=False para poder ver si hay challenges, o headless=True para server. 
    # Usaremos headless2=True que es el nuevo headless de Chrome que evade deteccion.
    driver = Driver(uc=True, headless=True, proxy=proxy_string)
    
    url = "https://www.reddit.com/r/Tinder/top.json?limit=10&t=week"
    print(f"Navegando a: {url}")
    driver.uc_open_with_reconnect(url, 10)
    
    # Esperamos que cargue
    time.sleep(random.uniform(5, 10))
    
    # Reddit en el navegador devuelve el JSON envuelto en un tag <pre>
    page_source = driver.page_source
    
    if "Failed to load" in page_source or "403 Forbidden" in page_source:
        print("ERROR 403: El WAF bloqueo la conexion.")
    else:
        try:
            # Extraer el texto del body
            json_text = driver.find_element("tag name", "pre").text
            data = json.loads(json_text)
            posts = data.get("data", {}).get("children", [])
            print(f"¡EXITO! WAF BYPASSED. Se extrajeron {len(posts)} posts.")
            
            with open("scratch/reddit_top_posts_sb.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("No se encontro un JSON valido. Es probable que haya caido en un Captcha o Challenge HTML.")
            print("Fragmento del HTML recibido:")
            print(page_source[:500])

except Exception as e:
    print(f"Error en SeleniumBase: {e}")
finally:
    if driver:
        driver.quit()
