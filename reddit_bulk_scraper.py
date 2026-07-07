import requests
import json
import os
import urllib.request
import time
from db_manager import insert_conversation

# Configuración Decodo Scraping API
DECODO_URL = "https://scraper-api.decodo.com/v2/scrape"
AUTH_HEADER = "Basic VTAwMDA0MjgwNjM6UFdfMWFkYWVlNTVkYzgzY2Q5ZTEwZWM4MjY0M2EyYTk3ODJm"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": AUTH_HEADER
}

def fetch_reddit_page(after_cursor=None):
    # Buscar posts con flairs de éxito y términos de citas/teléfonos
    query = "flair:success OR title:success OR title:date OR title:number OR title:whatsapp OR title:tinder"
    url = f"https://www.reddit.com/r/Tinder/search.json?q={query}&restrict_sr=1&sort=top&limit=100"
    if after_cursor:
        url += f"&after={after_cursor}"
        
    payload = {
        "target": "universal",
        "url": url
    }
    
    log_message(f"Llamando a Decodo Scraping API para URL: {url}")
    try:
        response = requests.post(DECODO_URL, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                content = data['results'][0].get('content', '')
                if content:
                    return json.loads(content)
        else:
            log_message(f"Error {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_message(f"Error realizando la petición Decodo: {e}")
    return None

def log_message(msg):
    print(msg)
    with open("scraper_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def download_image(url, folder, filename):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp, open(filepath, 'wb') as f:
            f.write(resp.read())
        return filepath
    except Exception as e:
        log_message(f"Error descargando {url}: {e}")
        return None

def main():
    if os.path.exists("scraper_log.txt"):
        os.remove("scraper_log.txt")
    log_message("Iniciando escaneo masivo de Reddit a través de Decodo...")
    
    target_carousels = 100
    target_texts = 100
    
    count_carousels = 0
    count_texts = 0
    count_single = 0
    
    after = None
    pages_scraped = 0
    
    os.makedirs("downloaded_files", exist_ok=True)
    
    while (count_carousels < target_carousels or count_texts < target_texts) and pages_scraped < 15:
        page_data = fetch_reddit_page(after)
        if not page_data:
            log_message("No se recibió respuesta válida del API. Abortando paginación.")
            break
            
        posts = page_data.get('data', {}).get('children', [])
        after = page_data.get('data', {}).get('after', None)
        
        log_message(f"Página {pages_scraped + 1} cargada. Publicaciones encontradas: {len(posts)}")
        if not posts:
            break
            
        for post in posts:
            p_data = post['data']
            post_id = p_data.get('id')
            title = p_data.get('title', 'Sin título')
            url = p_data.get('url', '')
            score = p_data.get('score', 0)
            created_utc = p_data.get('created_utc', 0)
            selftext = p_data.get('selftext', '')
            
            # Clasificar y procesar
            post_type = 'text_only'
            image_urls = []
            local_image_paths = []
            
            # 1. ¿Es carrusel (galería de imágenes)?
            if 'gallery_data' in p_data and 'media_metadata' in p_data:
                items = p_data['gallery_data'].get('items', [])
                metadata = p_data['media_metadata']
                if len(items) >= 2:
                    post_type = 'carousel'
                    for idx, item in enumerate(items):
                        media_id = item['media_id']
                        if media_id in metadata:
                            mime = metadata[media_id].get('m', '')
                            ext = 'png' if 'png' in mime else 'jpg'
                            img_url = f"https://i.redd.it/{media_id}.{ext}"
                            image_urls.append(img_url)
                            
                            # Descargar imagen local
                            folder = f"downloaded_files/post_{post_id}"
                            local_path = download_image(img_url, folder, f"img_{idx+1}.jpg")
                            if local_path:
                                local_image_paths.append(local_path)
                                
                    if local_image_paths:
                        count_carousels += 1
                        
            # 2. ¿Es una sola imagen?
            elif p_data.get('post_hint') == 'image' or url.endswith(('.jpg', '.png', '.jpeg')):
                post_type = 'single_image'
                image_urls.append(url)
                folder = f"downloaded_files/post_{post_id}"
                local_path = download_image(url, folder, "img_1.jpg")
                if local_path:
                    local_image_paths.append(local_path)
                    count_single += 1
                    
            # 3. ¿Es solo texto?
            else:
                if len(selftext.strip()) > 100:  # Asegurar que tenga suficiente contenido conversacional
                    post_type = 'text_only'
                    count_texts += 1
                else:
                    continue  # Ignorar si es muy corto o vacío
                    
            # Guardar en base de datos
            insert_conversation(
                post_id=post_id,
                title=title,
                url=url,
                score=score,
                post_type=post_type,
                body_text=selftext,
                image_urls=image_urls,
                local_image_paths=local_image_paths,
                created_utc=created_utc
            )
            
        log_message(f"Estado Actual -> Carruseles: {count_carousels}/{target_carousels} | Texto: {count_texts}/{target_texts} | 1 Imagen: {count_single}")
        pages_scraped += 1
        after = after  # Cursor para la siguiente página
        
        # Pequeña espera para no saturar
        time.sleep(2)
        
    log_message("\n--- Escaneo Completo! ---")
    log_message(f"Total Carruseles Guardados: {count_carousels}")
    log_message(f"Total Texto Puro Guardado: {count_texts}")
    log_message(f"Total 1 Imagen Guardado: {count_single}")

if __name__ == "__main__":
    main()
