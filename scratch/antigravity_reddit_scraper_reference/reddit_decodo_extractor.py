import json
import os
import urllib.request

try:
    with open('scratch/decodo_content.json', encoding='utf-8') as f:
        data = json.load(f)
        
    posts = data.get('data', {}).get('children', [])
    print(f"Total posts analizados: {len(posts)}")
    
    valid_cases = []
    
    for p in posts:
        post_data = p['data']
        title = post_data.get('title', 'Sin titulo')
        
        if 'gallery_data' in post_data and 'media_metadata' in post_data:
            items = post_data['gallery_data'].get('items', [])
            metadata = post_data['media_metadata']
            
            # Solo queremos casos con mas de 2 imagenes (carruseles de conversacion)
            if len(items) >= 2:
                images = []
                for item in items:
                    media_id = item['media_id']
                    if media_id in metadata:
                        mime = metadata[media_id].get('m', '')
                        ext = 'png' if 'png' in mime else 'jpg'
                        img_url = f"https://i.redd.it/{media_id}.{ext}"
                        images.append(img_url)
                
                valid_cases.append({
                    'title': title,
                    'images': images
                })
                
    print(f"Casos validos encontrados (>2 imagenes): {len(valid_cases)}")
    
    if len(valid_cases) > 0:
        base_dir = "casos_reales_tinder"
        os.makedirs(base_dir, exist_ok=True)
        
        # Guardar solo los 10 primeros
        for i, caso in enumerate(valid_cases[:10]):
            caso_dir = f"{base_dir}/caso_{i+1}"
            os.makedirs(caso_dir, exist_ok=True)
            
            print(f"Descargando Caso {i+1} ({len(caso['images'])} imagenes)")
            
            for j, img_url in enumerate(caso['images']):
                try:
                    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as resp, open(f"{caso_dir}/img_{j+1}.jpg", 'wb') as out_f:
                        out_f.write(resp.read())
                except Exception as e:
                    print(f"Error descargando {img_url}: {e}")
                    
        print("\n¡Extraccion finalizada con exito! Imagenes guardadas.")
    else:
        print("No se encontraron suficientes galerias en la primera pagina. Modificar el script para paginacion.")
except Exception as e:
    print(f"Error: {e}")
