import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update CSS to look like Tinder
tinder_css_updates = """
    :root {
        --bg-main: #f3f4f6; /* Lighter background like Tinder */
        --bg-card: #ffffff; /* White cards */
        --text-primary: #111827;
        --text-secondary: #6b7280;
        --accent-color: #fe3c72; /* Tinder Pink/Red */
        --glass-bg: rgba(255, 255, 255, 0.95);
        --glass-border: rgba(0, 0, 0, 0.05);
        --btn-primary: linear-gradient(45deg, #fd297b, #ff655b); /* Tinder Gradient */
        --btn-primary-hover: linear-gradient(45deg, #e0246b, #e65c52);
        
        --bubble-me: #3b82f6; /* Blue like iMessage/Tinder */
        --bubble-her: #f3f4f6; /* Gray for her */
        --bubble-her-text: #111827;
        
        --border-radius-lg: 20px;
    }
    
    body {
        background-color: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .chat-container {
        background: var(--bg-card);
        border: 1px solid var(--glass-border);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-radius: var(--border-radius-lg);
        overflow: hidden; /* Important for Tinder-like header */
    }
    
    /* Tinder Header */
    .game-header {
        background: var(--glass-bg);
        border-bottom: 1px solid var(--glass-border);
        color: var(--text-primary);
        padding: 15px 20px;
        position: relative;
    }
    
    /* Update bubbles */
    .bubble.player-bubble {
        background: var(--bubble-me);
        color: white;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .bubble.npc-bubble {
        background: var(--bubble-her);
        color: var(--bubble-her-text);
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .input-container {
        background: var(--bg-card);
        border-top: 1px solid var(--glass-border);
        padding: 15px;
    }
    
    .user-free-text {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        color: var(--text-primary);
        border-radius: 24px;
        padding: 12px 20px;
        resize: none;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .user-free-text::placeholder {
        color: #9ca3af;
    }
    
    .btn-send {
        background: var(--btn-primary);
        border-radius: 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: white;
    }
    
    /* Modal Coach adjustments */
    .coach-modal {
        background: #ffffff;
        color: #111827;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid #e5e7eb;
    }
    .coach-header {
        border-bottom: 1px solid #e5e7eb;
        color: #111827;
    }
    .coach-message {
        color: #374151;
    }
"""

# We need to find the existing :root and replace some vars, but it's safer to just append to <style>
if "</style>" in content:
    content = content.replace("</style>", tinder_css_updates + "\n</style>")

# 2. Add 'Enter' to submit listener in JS
# We need to find where evaluateSelection() is called, or just append the listener to DOMContentLoaded.
enter_js = """
    // Add Enter key listener to textarea
    document.addEventListener('DOMContentLoaded', () => {
        const textarea = document.getElementById('user-input');
        if(textarea) {
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault(); // Prevent new line
                    const btn = document.getElementById('btn-send');
                    if (btn && !btn.disabled) {
                        btn.click();
                    }
                }
            });
        }
    });
"""

if "</script>" in content:
    content = content.replace("</script>", enter_js + "\n</script>")


# 3. Dynamic Backend URL
# If file is local and they are on mobile, localhost won't work. 
# We'll just replace 'http://localhost:8000/api/evaluate' with a dynamic check.
dynamic_url_js = """
    let BACKEND_URL = 'http://localhost:8000/api/evaluate';
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '') {
        BACKEND_URL = `http://${window.location.hostname}:8000/api/evaluate`;
    } else if (window.location.protocol === 'file:' && /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        // If they open local file on mobile, they need to enter the PC's IP
        let savedIP = localStorage.getItem('backend_ip');
        if (!savedIP) {
            savedIP = prompt("Estás en celular. Ingresa la IP local de tu PC (ej: 192.168.1.5) para conectar al servidor:", "192.168.1.5");
            if (savedIP) {
                localStorage.setItem('backend_ip', savedIP);
            }
        }
        if (savedIP) {
            BACKEND_URL = `http://${savedIP}:8000/api/evaluate`;
        }
    }
    
    // Fallback for fetch in evaluateSelection (replace original string)
"""

if "http://localhost:8000/api/evaluate" in content:
    # First inject the BACKEND_URL definition at the top of script
    content = content.replace("let gameState = {", dynamic_url_js + "\n    let gameState = {")
    # Then replace the hardcoded string
    content = content.replace("'http://localhost:8000/api/evaluate'", "BACKEND_URL")
    content = content.replace('"http://localhost:8000/api/evaluate"', "BACKEND_URL")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("simulador_v1.2.html UI, Enter key, and Backend URL updated successfully.")
