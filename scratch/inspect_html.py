import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "user-free-text" in line or "textarea" in line or "options-container" in line:
        print(f"Line {i+1}: {line.strip()}")
        # print 20 lines before and after
        start = max(0, i-20)
        end = min(len(lines), i+25)
        print("--- SURROUNDING ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("-------------------\n")
