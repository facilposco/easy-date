import time
import os
from seleniumbase import Driver
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
import random, string
session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
proxy_string = f"{user}_session-{session_id}:{password}@{host}:{port}"

try:
    print("Iniciando SeleniumBase...")
    driver = Driver(uc=True, headless=True, proxy=proxy_string)
    url = "https://www.reddit.com/r/Tinder/top/?t=week"
    driver.uc_open_with_reconnect(url, 15)
    time.sleep(10)
    
    if "403 Forbidden" in driver.page_source:
        print("ERROR: WAF blocked.")
    else:
        print("WAF Bypassed. Haciendo scroll para cargar imagenes...")
        # Scroll para activar lazy loading de galerias
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(5)
        driver.execute_script("window.scrollBy(0, 2000);")
        time.sleep(5)
        
        with open("scratch/reddit_success_dom.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Extraer imagenes renderizadas
        imgs = driver.find_elements("tag name", "img")
        urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src")]
        
        gallery_urls = []
        for u in urls:
            if 'redd.it' in u and 'award' not in u and 'avatar' not in u:
                clean_u = u.split('?')[0].replace('preview.redd.it', 'i.redd.it')
                if clean_u not in gallery_urls:
                    gallery_urls.append(clean_u)
                    
        print(f"Encontradas {len(gallery_urls)} imagenes validas de posts de Reddit.")
        
        if len(gallery_urls) > 0:
            os.makedirs("casos_reales_tinder", exist_ok=True)
            import urllib.request
            for i, u in enumerate(gallery_urls[:15]): # Bajar 15 imagenes representativas
                try:
                    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as resp, open(f"casos_reales_tinder/img_extraida_{i+1}.jpg", "wb") as f:
                        f.write(resp.read())
                except Exception as e:
                    print(f"Error bajando {u}: {e}")
            print("Extraccion exitosa y guardada en la carpeta casos_reales_tinder.")
        else:
            print("El DOM se cargo pero no encontro tags IMG con redd.it")
except Exception as e:
    print(f"Error fatal: {e}")
finally:
    if 'driver' in locals() and driver:
        driver.quit()
