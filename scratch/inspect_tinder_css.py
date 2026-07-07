import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

def print_css(selector):
    idx = content.find(selector)
    if idx != -1:
        end = content.find("}", idx)
        print(content[idx:end+1])

print_css(".input-container {")
print_css(".user-free-text {")
print_css(".btn-send {")
print_css(".message.user .bubble {")
print_css(".message.her .bubble {")
print_css(".top-bar {")
