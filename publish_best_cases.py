import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "textgame.db"
HTML_PATH = "estudio_textgame_casos_reales.html"

def get_best_cases():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 10 Mejores Carruseles (Ordenados por fecha más reciente)
    cursor.execute("""
    SELECT post_id, title, url, score, body_text, image_urls, local_image_paths, created_utc 
    FROM reddit_conversations 
    WHERE post_type = 'carousel' 
    ORDER BY created_utc DESC 
    LIMIT 10;
    """)
    carousels = cursor.fetchall()
    
    # 2. 10 Mejores Texto Puro (Ordenados por fecha más reciente)
    cursor.execute("""
    SELECT post_id, title, url, score, body_text, image_urls, local_image_paths, created_utc 
    FROM reddit_conversations 
    WHERE post_type = 'text_only' 
    ORDER BY created_utc DESC 
    LIMIT 10;
    """)
    texts = cursor.fetchall()
    
    conn.close()
    return carousels, texts

def format_date(utc_timestamp):
    if not utc_timestamp:
        return "N/A"
    return datetime.fromtimestamp(utc_timestamp).strftime('%Y-%m-%d')

def parse_text_to_chat(body_text):
    lines = body_text.split('\n')
    chat_html = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Identificar si habla el hombre o la mujer
        lower_line = line.lower()
        if lower_line.startswith(("me:", "him:", "yo:", "él:", "el:")):
            cleaned = line.split(':', 1)[1].strip()
            chat_html += f'<div class="bubble bubble-me" style="margin-left: auto; max-width: 80%; background: var(--bubble-me); color: white; padding: 8px 12px; border-radius: 12px 12px 2px 12px; margin-bottom: 8px; font-size: 0.95rem;">{cleaned}</div>'
        elif lower_line.startswith(("her:", "she:", "ella:")):
            cleaned = line.split(':', 1)[1].strip()
            chat_html += f'<div class="bubble bubble-her" style="margin-right: auto; max-width: 80%; background: var(--bubble-her); color: white; padding: 8px 12px; border-radius: 12px 12px 12px 2px; margin-bottom: 8px; font-size: 0.95rem;">{cleaned}</div>'
        else:
            chat_html += f'<div style="text-align: center; color: var(--text-secondary); font-size: 0.8rem; margin: 4px 0;">{line}</div>'
    return chat_html

def main():
    print("Recuperando los mejores casos de la base de datos...")
    carousels, texts = get_best_cases()
    
    # Renderizar Carruseles
    carousel_html_cards = '<h3 style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; margin-top: 20px; font-family: \'Outfit\'; font-size:1.3rem;">Conversaciones con Carrusel (Deslizar horizontalmente)</h3>'
    for idx, c in enumerate(carousels):
        post_id, title, url, score, body_text, img_urls_json, local_paths_json, created_utc = c
        date_str = format_date(created_utc)
        local_paths = json.loads(local_paths_json) if local_paths_json else []
        
        # Si no hay imágenes locales por algún error, usar URLs originales de Reddit
        display_paths = local_paths if local_paths else (json.loads(img_urls_json) if img_urls_json else [])
        
        img_tags = "".join([f'<img class="reddit-img" src="{p}" style="max-height: 480px; width: auto; flex-shrink: 0; border-radius: 8px; border: 1px solid var(--glass-border);">' for p in display_paths])
        
        card = f"""
        <div class="case-card" id="carousel-{post_id}">
            <div class="case-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                <h2 style="font-size: 1.15rem; margin: 0;">#{idx+1} - {title} <span class="score" style="color: var(--accent-color); font-size:0.85rem;">[Score: {score}/10]</span></h2>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">{date_str}</span>
                    <a href="{url}" target="_blank" style="color: #60a5fa; font-size: 0.8rem; text-decoration: none;">🔗 Link</a>
                </div>
            </div>
            <div class="split-container" style="display: flex; flex-direction: column; gap: 15px; margin-top: 15px;">
                <div class="screenshot-side" style="display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; width: 100%; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;">
                    {img_tags}
                </div>
                {f'<div class="analysis-box" style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; border: 1px solid var(--glass-border); font-size:0.92rem;"><strong style="color:var(--accent-color);">Análisis Contextual:</strong> {body_text}</div>' if body_text.strip() else ''}
            </div>
        </div>
        """
        carousel_html_cards += card
        
    # Renderizar Texto Puro
    text_html_cards = '<h3 style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; margin-top: 20px; font-family: \'Outfit\'; font-size:1.3rem;">Conversaciones Sin Imagen (Solo texto)</h3>'
    for idx, t in enumerate(texts):
        post_id, title, url, score, body_text, _, _, created_utc = t
        date_str = format_date(created_utc)
        chat_bubbles = parse_text_to_chat(body_text)
        
        card = f"""
        <div class="case-card" id="text-{post_id}">
            <div class="case-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                <h2 style="font-size: 1.15rem; margin: 0;">#{idx+1} - {title} <span class="score" style="color: var(--accent-color); font-size:0.85rem;">[Score: {score}/10]</span></h2>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">{date_str}</span>
                    <a href="{url}" target="_blank" style="color: #60a5fa; font-size: 0.8rem; text-decoration: none;">🔗 Link</a>
                </div>
            </div>
            <div class="text-chat-container" style="margin-top: 15px; background: rgba(0, 0, 0, 0.25); border: 1px solid var(--glass-border); border-radius: 12px; padding: 15px; display: flex; flex-direction: column; gap: 4px; max-height: 400px; overflow-y: auto;">
                {chat_bubbles}
            </div>
        </div>
        """
        text_html_cards += card

    # Leer el HTML actual
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Reemplazar el bloque #reddit-carrusel
    start_tag_car = '<div id="reddit-carrusel" class="sub-tab-content" style="display: none;">'
    end_tag_car = '</div>'
    
    # Encontrar la sección de carrusel
    idx_car = html_content.find(start_tag_car)
    if idx_car != -1:
        idx_car_end = html_content.find(end_tag_car, idx_car + len(start_tag_car))
        if idx_car_end != -1:
            old_car_block = html_content[idx_car:idx_car_end + len(end_tag_car)]
            new_car_block = f'{start_tag_car}\n{carousel_html_cards}\n{end_tag_car}'
            html_content = html_content.replace(old_car_block, new_car_block)
            print("Carruseles insertados correctamente en el HTML.")

    # Reemplazar el bloque #reddit-sin-imagen
    start_tag_txt = '<div id="reddit-sin-imagen" class="sub-tab-content" style="display: none;">'
    end_tag_txt = '</div>'
    
    idx_txt = html_content.find(start_tag_txt)
    if idx_txt != -1:
        idx_txt_end = html_content.find(end_tag_txt, idx_txt + len(start_tag_txt))
        if idx_txt_end != -1:
            old_txt_block = html_content[idx_txt:idx_txt_end + len(end_tag_txt)]
            new_txt_block = f'{start_tag_txt}\n{text_html_cards}\n{end_tag_txt}'
            html_content = html_content.replace(old_txt_block, new_txt_block)
            print("Hilos de texto insertados correctamente en el HTML.")

    # Guardar cambios
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("¡estudio_textgame_casos_reales.html actualizado con éxito!")

if __name__ == "__main__":
    main()
