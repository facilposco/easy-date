import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# I will move the BACKEND_URL logic to the VERY TOP of the script tag.
# First, remove it from the bottom.
safe_js_backend = """    // Dynamic Backend URL for Mobile
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
    }"""

if safe_js_backend in content:
    content = content.replace(safe_js_backend, "")

# Now insert var BACKEND_URL at the beginning of <script>
top_js = """<script>
    var BACKEND_URL = 'http://localhost:8000/api/evaluate';
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '') {
        BACKEND_URL = `http://${window.location.hostname}:8000/api/evaluate`;
    } else if (window.location.protocol === 'file:' && /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        var savedIP = localStorage.getItem('backend_ip');
        if (!savedIP) {
            savedIP = prompt("Celular detectado. Ingresa la IP local de tu PC (ej: 192.168.1.5):", "192.168.1.5");
            if (savedIP) {
                localStorage.setItem('backend_ip', savedIP);
            }
        }
        if (savedIP) {
            BACKEND_URL = `http://${savedIP}:8000/api/evaluate`;
        }
    }
"""

content = content.replace("<script>", top_js)

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("BACKEND_URL moved to the top of the script with var.")
