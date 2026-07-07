import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

proxy_config = {
    "server": f"http://{host}:{port}",
    "username": user,
    "password": password
}

async def main():
    async with async_playwright() as p:
        print("Lanzando Chromium con Playwright Stealth...")
        # Intentamos en headless=True. Si falla, el headless=False a veces tiene distinta huella.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            proxy=proxy_config,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Aplicar Stealth
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.reddit.com/r/Tinder/top.json?limit=10&t=week"
        print(f"Navegando a: {url}")
        
        response = await page.goto(url, wait_until="domcontentloaded")
        print(f"Status HTTP: {response.status if response else 'Unknown'}")
        
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        
        if "403 Forbidden" in content or (response and response.status == 403):
            print("ERROR 403: El WAF bloqueo la conexion en Playwright.")
        else:
            try:
                json_text = await page.locator("pre").inner_text()
                data = json.loads(json_text)
                posts = data.get("data", {}).get("children", [])
                print(f"¡EXITO! WAF BYPASSED. Se extrajeron {len(posts)} posts.")
                
                with open("scratch/reddit_top_posts_pw.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print("No se encontro JSON. Respuesta del WAF (Fragmento):")
                print(content[:500])
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
