import asyncio
import os
import random
import string
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

async def run_scraping_probe():
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user_session = f"{user}_session-{session_id}"
    
    proxy_config = {
        "server": f"http://{host}:{port}",
        "username": user_session,
        "password": password
    }
    
    print(f"Probando Playwright Stealth con IP rotada: {user_session}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_config
        )
        
        # Crear contexto con User-Agent moderno y lenguaje calibrado
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-ES,es;q=0.9",
            timezone_id="Europe/Madrid"
        )
        
        page = await context.new_page()
        
        # Aplicar stealth
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.reddit.com/r/Tinder/top.json?limit=1"
        try:
            response = await page.goto(url, timeout=30000)
            print(f"Status recibido: {response.status if response else 'Sin respuesta'}")
            
            content = await page.content()
            os.makedirs("scratch", exist_ok=True)
            with open("scratch/playwright_test_output.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"Tamaño del HTML recibido: {len(content)} bytes")
            if response and response.status == 200:
                print("¡CONEXION EXITOSA A REDDIT JSON!")
                # Intentar parsear el JSON
                text = await page.locator("body").inner_text()
                try:
                    json_data = json.loads(text)
                    print("JSON cargado exitosamente.")
                except Exception:
                    print("El cuerpo no es JSON plano, posiblemente HTML renderizado en visor de Chrome.")
            else:
                print("Conexión rechazada o WAF bloqueó la petición.")
                
        except Exception as e:
            print("Error durante la petición:", e)
            
        await browser.close()

if __name__ == "__main__":
    import json
    asyncio.run(run_scraping_probe())
