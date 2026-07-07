import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "gameData" in line or "levels" in line:
        if "console" not in line and len(line) < 300:
            print(f"Line {i+1}: {line.strip()}")
