import requests
import re
import xml.etree.ElementTree as ET
import os
import json
import sys

# Forzar codificación de consola a UTF-8 para evitar errores de emojis en Windows
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

url = "https://www.reddit.com/r/tinder/search.rss?q=smooth+OR+success+OR+number&restrict_sr=on&sort=top&t=all"
print(f"Buscando posts en: {url}")

try:
    r = requests.get(url, headers=headers, proxies=proxies, timeout=15)
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        exit()
        
    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(r.content)
    
    entries = root.findall('atom:entry', namespaces)
    print(f"Se encontraron {len(entries)} entradas.")
    
    downloaded = 0
    metadata = []
    
    for entry in entries:
        if downloaded >= 2:
            break
            
        title_el = entry.find('atom:title', namespaces)
        title = title_el.text if title_el is not None else "Sin Título"
        
        link_el = entry.find('atom:link', namespaces)
        post_link = link_el.attrib.get('href') if link_el is not None else ""
        
        content_el = entry.find('atom:content', namespaces)
        content_text = content_el.text if content_el is not None else ""
        
        img_match = re.search(r'href="([^"]*?redd\.it/[^"]*?\.(?:jpg|png|jpeg))"', content_text)
        if not img_match:
            img_match = re.search(r'(https://i\.redd\.it/[^\s"<>]+?\.(?:jpg|png|jpeg))', content_text)
            
        if img_match:
            img_url = img_match.group(1) if img_match.lastindex else img_match.group(0)
            
            # Limpiar caracteres raros para impresión segura
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"\nProcesando post: {safe_title}")
            print(f"Imagen: {img_url}")
            
            # Descargar imagen
            img_r = requests.get(img_url, headers=headers, proxies=proxies, timeout=10)
            if img_r.status_code == 200:
                os.makedirs("reddit_images", exist_ok=True)
                ext = os.path.splitext(img_url.split('?')[0])[1]
                if not ext:
                    ext = ".jpg"
                filename = f"reddit_images/reddit_post_{downloaded + 1}{ext}"
                with open(filename, 'wb') as f:
                    f.write(img_r.content)
                
                print(f"Imagen guardada en: {filename}")
                
                metadata.append({
                    "id": downloaded + 1,
                    "title": title,
                    "post_url": post_link,
                    "image_path": filename,
                    "image_url": img_url
                })
                downloaded += 1
            else:
                print(f"No se pudo descargar la imagen, status: {img_r.status_code}")
                
    with open("scratch/reddit_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    print(f"\nMetadatos guardados en scratch/reddit_metadata.json")
    
except Exception as e:
    print(f"Error: {e}")
