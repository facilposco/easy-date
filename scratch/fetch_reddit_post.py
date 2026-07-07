import requests
import json
import os

def fetch_one_reddit_post():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Inyectar proxy de DataImpulse
    proxies = {
        'http': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823',
        'https': 'http://b1bf7cccb79805e29868:0f98e1edfd0fac2f@gw.dataimpulse.com:823'
    }
    
    url = "https://www.reddit.com/r/tinder/hot.json?limit=10"
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code != 200:
            print(f"Error accediendo a Reddit: {response.status_code}")
            return
            
        data = response.json()
        posts = data.get('data', {}).get('children', [])
        
        for post in posts:
            post_data = post.get('data', {})
            post_url = post_data.get('url', '')
            title = post_data.get('title', '')
            permalink = post_data.get('permalink', '')
            
            if post_url.endswith(('.jpg', '.png', '.jpeg')) and "reddit.com" not in post_url:
                print("--- Post Encontrado ---")
                print(f"Título: {title}")
                print(f"URL de la Imagen: {post_url}")
                print(f"Enlace Reddit: https://www.reddit.com{permalink}")
                
                img_response = requests.get(post_url, headers=headers, proxies=proxies, timeout=10)
                if img_response.status_code == 200:
                    os.makedirs("reddit_images", exist_ok=True)
                    filename = os.path.join("reddit_images", os.path.basename(post_url))
                    with open(filename, 'wb') as f:
                        f.write(img_response.content)
                    print(f"Imagen descargada con éxito en: {filename}")
                    return
                else:
                    print("No se pudo descargar la imagen")
    except Exception as e:
        print(f"Error: {e}")
                
fetch_one_reddit_post()
