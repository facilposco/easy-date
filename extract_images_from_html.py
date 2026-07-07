import json
from bs4 import BeautifulSoup
import re
import urllib.parse
import os

try:
    with open('scratch/reddit_html_test.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    posts = soup.find_all('shreddit-post')
    
    print(f"Posts encontrados: {len(posts)}")
    galleries = []
    
    for post in posts:
        # Check if it has a gallery (multiple images)
        gallery_elements = post.find_all('ul') # Galleries are often in ULs inside shreddit-post
        images = post.find_all('img')
        
        # Valid images are usually preview.redd.it or i.redd.it
        img_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src') or ""
            if 'redd.it' in src and 'award' not in src:
                # Limpiar la URL de los parametros de resize de preview.redd.it
                clean_url = src.split('?')[0].replace('preview.redd.it', 'i.redd.it')
                if clean_url not in img_urls:
                    img_urls.append(clean_url)
        
        # We only want posts with > 2 images
        if len(img_urls) >= 2:
            title = post.get('post-title', 'Sin titulo')
            galleries.append({
                'title': title,
                'images': img_urls
            })
            
    print(f"Encontrados {len(galleries)} posts con multiples imagenes.")
    
    if len(galleries) > 0:
        os.makedirs("casos_reales_tinder", exist_ok=True)
        import urllib.request
        
        print("Descargando las primeras imagenes del primer caso...")
        for i, g in enumerate(galleries[:10]):
            print(f"Descargando Caso {i+1}: {g['title']}")
            folder = f"casos_reales_tinder/caso_{i+1}"
            os.makedirs(folder, exist_ok=True)
            for j, img_url in enumerate(g['images']):
                try:
                    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response, open(f"{folder}/img_{j+1}.jpg", 'wb') as out_file:
                        data = response.read()
                        out_file.write(data)
                except Exception as e:
                    print(f"Error bajando {img_url}: {e}")
        print("Scraping finalizado.")
    else:
        print("No se encontraron galerias. Intentemos extraer del json del state.")
        data_script = soup.find('faceplate-tracker')
        print("Data tags:", data_script)
except Exception as e:
    print(f"Error: {e}")
