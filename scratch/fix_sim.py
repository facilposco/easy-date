import re

def fix_html(filepath, content):
    # Fix 1: Match modal photo. Let's find showMatchModal()
    # It probably has something like `document.getElementById('match-girl-img').style.backgroundImage = 'url(' + level.avatarUrl + ')';`
    # Or maybe it's not setting it at all. Let's see if we can find it.
    
    # Actually, I can just replace the buttons first.
    btn_send_regex = r'(<button class="btn-send" id="btn-send".*?>ENVIAR RESPUESTA</button>)\s*<div style="display: flex; gap: 10px; margin-top: 10px;">\s*(<button onclick="showScreen\(\'study\'\).*?</button>)\s*(<button onclick="resetGame\(\)".*?</button>)\s*</div>'
    
    def repl_buttons(m):
        btn_send = m.group(1).replace('height: 46px;', 'height: 54px;').replace('font-size: 1.05rem;', 'font-size: 1.15rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;')
        btn_study = m.group(2)
        btn_reset = m.group(3)
        return f"""
<div style="display: flex; gap: 10px; margin-bottom: 10px; justify-content: flex-end;">
    {btn_reset}
    {btn_study}
</div>
{btn_send}"""
    
    new_content = re.sub(btn_send_regex, repl_buttons, content, flags=re.DOTALL)
    
    if new_content == content:
        print("Failed to replace buttons.")
    else:
        print("Replaced buttons.")

    # Fix 3: Casos reales iframe to inline content
    # The iframe is likely `<iframe id="study-iframe" src="propuesta_conversaciones.html" style="width: 100%; height: 100%; border: none;"></iframe>`
    # Let's read propuesta_conversaciones.html and extract its body or main content.
    try:
        with open('propuesta_conversaciones.html', 'r', encoding='utf-8') as f:
            propuesta = f.read()
            # Extract everything between <body> and </body>
            body_match = re.search(r'<body[^>]*>(.*?)</body>', propuesta, flags=re.DOTALL | re.IGNORECASE)
            if body_match:
                inner_content = body_match.group(1)
                # Replace iframe with this content, wrapped in a scrollable div
                iframe_regex = r'<iframe[^>]*id="study-iframe"[^>]*></iframe>'
                replacement = f'<div id="study-iframe-container" style="width: 100%; height: 100%; overflow-y: auto; background: white; border-radius: 20px;">{inner_content}</div>'
                new_content = re.sub(iframe_regex, replacement, new_content)
                print("Replaced iframe with inline content from propuesta_conversaciones.html")
            else:
                print("Could not find body in propuesta_conversaciones.html")
    except Exception as e:
        print("Error reading propuesta_conversaciones.html:", e)
        
    return new_content

if __name__ == "__main__":
    filepath = 'simulador_v1.0.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = fix_html(filepath, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
