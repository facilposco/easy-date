# -*- coding: utf-8 -*-
import re

with open('estudio_textgame_casos_reales.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
bubbles_with_lines = []

for idx, line in enumerate(lines):
    # Buscar burbujas en la línea
    match = re.search(r'<div class="bubble\s+([^"]+)">([^<]*)<div class="msg-time">', line)
    if match:
        b_class = match.group(1)
        b_text = match.group(2)
        bubbles_with_lines.append((idx + 1, b_class, b_text))

with open('scratch/extracted_bubbles.txt', 'w', encoding='utf-8') as out:
    for line_num, b_class, b_text in bubbles_with_lines:
        out.write(f"L{line_num} | {b_class} | {b_text.strip()}\n")

print(f"Extracted {len(bubbles_with_lines)} bubbles to scratch/extracted_bubbles.txt")
