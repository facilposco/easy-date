import re

def fix_html(filepath, content):
    # Fix 4: Replace buttons layout
    # Current structure:
    # <button class="btn-send" id="btn-send" ...>ENVIAR RESPUESTA</button>
    # <div style="display: flex; gap: 8px; width: 100%;">
    #     <button onclick="showScreen('study')" ...>📚 Estudiar Casos</button>
    #     <button onclick="resetGame()" ...>Reiniciar</button>
    # </div>
    btn_send_regex = r'(<button class="btn-send" id="btn-send"[^>]*>ENVIAR RESPUESTA</button>)\s*<div style="display: flex; gap: 8px; width: 100%;">\s*(<button onclick="showScreen\(\'study\'\)[^>]*>.*?</button>)\s*(<button onclick="resetGame\(\)"[^>]*>.*?</button>)\s*</div>'
    
    def repl_buttons(m):
        btn_send = m.group(1).replace('height: 46px;', 'height: 54px;').replace('font-size: 1.05rem;', 'font-size: 1.15rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;')
        btn_study = m.group(2).replace('flex: 7;', 'flex: 4; font-size: 0.75rem;')
        btn_reset = m.group(3).replace('flex: 3;', 'flex: 2; font-size: 0.75rem;')
        return f"""<div style="display: flex; gap: 8px; width: 100%; margin-bottom: 8px; justify-content: flex-end;">
    {btn_reset}
    {btn_study}
</div>
{btn_send}"""
    
    new_content = re.sub(btn_send_regex, repl_buttons, content, flags=re.DOTALL)
    
    if new_content == content:
        print("Failed to replace buttons.")
    else:
        print("Replaced buttons.")
        
    return new_content

if __name__ == "__main__":
    filepath = 'simulador_v1.0.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = fix_html(filepath, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
