import sys

sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Locate the injected Tinder CSS (starts with ":root {" and has "Tinder Pink/Red")
start_str = "    :root {\n        --bg-main: #f3f4f6; /* Lighter background like Tinder */"
end_str = "    .coach-message {\n        color: #374151;\n    }\n"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx + len(end_str):]
    print("Injected CSS removed.")
else:
    print("Could not find injected CSS block.")
    
# Find the enter_js block
js_str = """
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
if js_str in content:
    content = content.replace(js_str, "")
    print("Injected enter JS removed.")

# Find dynamic backend url
dynamic_js = """    let BACKEND_URL = 'http://localhost:8000/api/evaluate';
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
if dynamic_js in content:
    content = content.replace(dynamic_js, "")
    print("Dynamic URL JS removed.")

if "BACKEND_URL" in content:
    content = content.replace("BACKEND_URL", "'http://localhost:8000/api/evaluate'")
    print("BACKEND_URL variables restored.")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)
