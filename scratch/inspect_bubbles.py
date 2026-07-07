# -*- coding: utf-8 -*-
import re
import sys

# Forzar salida en utf-8 en Windows
sys.stdout.reconfigure(encoding='utf-8')

with open('estudio_textgame_casos_reales.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar todos los bloques de case-card
cards = re.findall(r'<div class="case-card">.*?<h2>(.*?)</h2>.*?<div class="chat-container">(.*?)</div>.*?</div>', content, re.DOTALL)

for i, (title, chat_block) in enumerate(cards):
    print(f"\n--- CASO {i+1}: {title.strip()} ---")
    bubbles = re.findall(r'<div class="bubble\s+([^"]+)">([^<]+)<', chat_block)
    for b_type, text in bubbles[:20]:  # Mostrar los primeros 20 mensajes
        print(f"  [{b_type}]: {text.strip()}")
