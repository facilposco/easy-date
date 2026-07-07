import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Let's check how the fetch was replaced
idx = content.find("fetch(BACKEND_URL")
if idx != -1:
    print("FETCH BLOCK:")
    print(content[idx-100:idx+200])
else:
    print("fetch(BACKEND_URL NOT FOUND")

# Let's check where BACKEND_URL is defined
idx = content.find("let BACKEND_URL")
if idx != -1:
    print("\nBACKEND_URL DEF:")
    print(content[idx-50:idx+200])
else:
    print("\nBACKEND_URL NOT FOUND")
