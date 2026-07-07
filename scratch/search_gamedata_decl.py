import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("gameData")
while idx != -1:
    line_no = content[:idx].count("\n") + 1
    line = content.split("\n")[line_no-1]
    print(f"Line {line_no}: {line[:100]}... [Total length: {len(line)}]")
    idx = content.find("gameData", idx + 1)
