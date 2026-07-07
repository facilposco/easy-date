import sys
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# I will fix the 'user-input' -> 'user-free-text' bug first.
content = content.replace("document.getElementById('user-input')", "document.getElementById('user-free-text')")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Replaced user-input with user-free-text in JS.")
