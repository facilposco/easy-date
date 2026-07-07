import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.1.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(1800, min(len(lines), 1940)):
    print(f"{i+1}: {lines[i].rstrip()}")
