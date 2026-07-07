import os
import random
import time
from dotenv import load_dotenv
from seleniumbase import Driver

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
proxy_string = f"{user}:{password}@{host}:{port}"

try:
    print("Iniciando SeleniumBase...")
    driver = Driver(uc=True, headless=True, proxy=proxy_string)
    url = "https://www.reddit.com/r/Tinder/top/?t=week"
    print(f"Navegando al HTML: {url}")
    driver.uc_open_with_reconnect(url, 10)
    time.sleep(10)
    
    page_source = driver.page_source
    if "403 Forbidden" in page_source or "blocked" in page_source.lower() or "cloudflare" in page_source.lower():
        print("ERROR: El HTML tambien esta bloqueado o mostro Cloudflare Challenge.")
    else:
        print("EXITO HTML CARGADO. Salvando...")
    
    # Salvar screenshot de todos modos para ver que vio el navegador
    driver.save_screenshot("scratch/reddit_html_test.png")
    with open("scratch/reddit_html_test.html", "w", encoding="utf-8") as f:
        f.write(page_source)
        
    print("Screenshot y HTML salvados en scratch/")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'driver' in locals() and driver:
        driver.quit()
