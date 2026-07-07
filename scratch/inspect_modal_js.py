import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("function showCoachModal")
if idx != -1:
    end_idx = content.find("}", idx)
    end_idx = content.find("}", end_idx + 1)
    print("CODE:\n" + content[idx:end_idx+30])
