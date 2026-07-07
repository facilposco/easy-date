import requests
import re
import xml.etree.ElementTree as ET
import os
import json
import sys

# Configurar logs
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

proxies = {
    'http': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823',
    'https': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823'
}

def clean_title(title):
    return title.encode('ascii', 'ignore').decode('ascii')

def scrape_reddit():
    queries = ["smooth", "success", "got her number", "cringe", "flirting", "opening line"]
    single_image_posts = []
    multi_image_posts = []
    
    os.makedirs("reddit_images", exist_ok=True)
    seen_urls = set()
    
    for query in queries:
        if len(single_image_posts) >= 10 and len(multi_image_posts) >= 10:
            break
            
        url = f"https://www.reddit.com/r/tinder/search.rss?q={query}&restrict_sr=on&sort=top&t=all&limit=100"
        logging.info(f"Buscando: {url}")
        
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            if r.status_code != 200:
                logging.error(f"Error {r.status_code} buscando {query}")
                continue
                
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            root = ET.fromstring(r.content)
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                title_el = entry.find('atom:title', namespaces)
                title = title_el.text if title_el is not None else "Sin Título"
                
                link_el = entry.find('atom:link', namespaces)
                post_link = link_el.attrib.get('href') if link_el is not None else ""
                
                if post_link in seen_urls:
                    continue
                seen_urls.add(post_link)
                
                content_el = entry.find('atom:content', namespaces)
                content_text = content_el.text if content_el is not None else ""
                
                # Buscar todos los enlaces a i.redd.it en la entrada
                img_urls = re.findall(r'href="([^"]*?i\.redd\.it/[^"]*?\.(?:jpg|png|jpeg))"', content_text)
                if not img_urls:
                    img_urls = re.findall(r'(https://i\.redd\.it/[^\s"<>]+?\.(?:jpg|png|jpeg))', content_text)
                
                # Eliminar duplicados manteniendo orden
                img_urls = list(dict.fromkeys(img_urls))
                
                if not img_urls:
                    continue
                
                # Clasificar
                if len(img_urls) == 1:
                    if len(single_image_posts) < 10:
                        single_image_posts.append({
                            "title": title,
                            "post_url": post_link,
                            "img_urls": img_urls
                        })
                        logging.info(f"Encontrado Single Image ({len(single_image_posts)}/10): {clean_title(title)}")
                else:
                    if len(multi_image_posts) < 10:
                        multi_image_posts.append({
                            "title": title,
                            "post_url": post_link,
                            "img_urls": img_urls
                        })
                        logging.info(f"Encontrado Multi Image ({len(multi_image_posts)}/10): {clean_title(title)} con {len(img_urls)} imágenes")
                        
        except Exception as e:
            logging.error(f"Error procesando query {query}: {e}")
            
    # Descargar imágenes y guardar metadata
    logging.info("📥 Iniciando descarga de imágenes...")
    
    # 1. Descargar Single-Image Posts
    reddit_metadata = []
    for idx, post in enumerate(single_image_posts):
        img_url = post["img_urls"][0]
        ext = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
        filename = f"reddit_images/single_{idx+1}{ext}"
        
        try:
            img_r = requests.get(img_url, headers=headers, proxies=proxies, timeout=10)
            if img_r.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(img_r.content)
                reddit_metadata.append({
                    "id": f"single_{idx+1}",
                    "type": "single",
                    "title": post["title"],
                    "post_url": post["post_url"],
                    "image_paths": [filename],
                    "image_urls": [img_url]
                })
                logging.info(f"Descargado: {filename}")
            else:
                logging.error(f"Error descargando {img_url}: {img_r.status_code}")
        except Exception as e:
            logging.error(f"Excepción descargando {img_url}: {e}")

    # 2. Descargar Multi-Image Posts (Galerías)
    for idx, post in enumerate(multi_image_posts):
        downloaded_paths = []
        downloaded_urls = []
        for img_idx, img_url in enumerate(post["img_urls"][:4]): # Límite de 4 imágenes por carrusel para no saturar
            ext = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
            filename = f"reddit_images/multi_{idx+1}_{img_idx+1}{ext}"
            
            try:
                img_r = requests.get(img_url, headers=headers, proxies=proxies, timeout=10)
                if img_r.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(img_r.content)
                    downloaded_paths.append(filename)
                    downloaded_urls.append(img_url)
                    logging.info(f"Descargado: {filename}")
                else:
                    logging.error(f"Error descargando {img_url}: {img_r.status_code}")
            except Exception as e:
                logging.error(f"Excepción descargando {img_url}: {e}")
                
        if downloaded_paths:
            reddit_metadata.append({
                "id": f"multi_{idx+1}",
                "type": "multi",
                "title": post["title"],
                "post_url": post["post_url"],
                "image_paths": downloaded_paths,
                "image_urls": downloaded_urls
            })
            
    with open("scratch/reddit_deep_metadata.json", "w", encoding="utf-8") as f:
        json.dump(reddit_metadata, f, indent=4, ensure_ascii=False)
        
    logging.info("🏁 Descargas finalizadas. Metadata guardada en scratch/reddit_deep_metadata.json")

if __name__ == "__main__":
    scrape_reddit()
