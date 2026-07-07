import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find(".coach-modal {")
if idx != -1:
    end_idx = content.find("}", idx)
    print("MODAL CSS:\n" + content[idx:end_idx+1])

idx = content.find(".coach-message {")
if idx != -1:
    end_idx = content.find("}", idx)
    print("\nMESSAGE CSS:\n" + content[idx:end_idx+1])
