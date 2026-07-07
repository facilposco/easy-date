import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.1.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find(".chat-container {")
if idx != -1:
    end_idx = content.find("}", idx)
    print("ORIGINAL chat-container:\n" + content[idx:end_idx+1])
