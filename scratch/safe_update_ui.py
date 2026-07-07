import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update CSS Variables ONLY, do not touch structural classes
safe_css = """
    /* Tinder UI Enhancements (Colors only) */
    :root {
        --bubble-me: #3b82f6; /* Azul Tinder/iMessage */
        --bubble-her: #f3f4f6; /* Gris Claro */
    }
    
    .bubble.player-bubble {
        background: var(--bubble-me);
        color: white;
        border-radius: 20px 20px 4px 20px;
    }
    
    .bubble.npc-bubble {
        background: var(--bubble-her);
        color: #111827;
        border-radius: 20px 20px 20px 4px;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .game-header {
        background: linear-gradient(180deg, rgba(254,60,114,0.15) 0%, rgba(0,0,0,0) 100%);
        border-bottom: 1px solid rgba(254,60,114,0.2);
    }
    
    .btn-send {
        background: linear-gradient(45deg, #fd297b, #ff655b);
        color: white;
        font-weight: bold;
        border: none;
    }
"""

if "Tinder UI Enhancements" not in content:
    content = content.replace("</style>", safe_css + "\n</style>")

# 2. Add safe dynamic URL and Enter Key logic at the END of the script
safe_js = """
    // --- TINDER UI & MOBILE FIXES ---
    
    // Dynamic Backend URL for Mobile
    let BACKEND_URL = 'http://localhost:8000/api/evaluate';
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '') {
        BACKEND_URL = `http://${window.location.hostname}:8000/api/evaluate`;
    } else if (window.location.protocol === 'file:' && /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        let savedIP = localStorage.getItem('backend_ip');
        if (!savedIP) {
            savedIP = prompt("Celular detectado (Offline). Ingresa la IP local de tu PC (ej: 192.168.1.5) para conectar al servidor de inteligencia artificial:", "192.168.1.5");
            if (savedIP) {
                localStorage.setItem('backend_ip', savedIP);
            }
        }
        if (savedIP) {
            BACKEND_URL = `http://${savedIP}:8000/api/evaluate`;
        }
    }

    // Enter Key Listener
    document.addEventListener('DOMContentLoaded', () => {
        const textarea = document.getElementById('user-input');
        if(textarea) {
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault(); 
                    const btn = document.getElementById('btn-send');
                    if (btn && !btn.disabled) {
                        btn.click();
                    }
                }
            });
        }
    });
"""

if "TINDER UI & MOBILE FIXES" not in content:
    content = content.replace("</script>", safe_js + "\n</script>")

# 3. Replace the hardcoded fetch URL with the variable
if "fetch('http://localhost:8000/api/evaluate'" in content:
    content = content.replace("fetch('http://localhost:8000/api/evaluate'", "fetch(BACKEND_URL")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Applied Safe CSS and JS updates successfully.")
