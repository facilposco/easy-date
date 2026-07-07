import sys

sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("<script>")
if idx != -1:
    print("SCRIPT START:\n" + content[idx:idx+800])
