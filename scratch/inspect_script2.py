import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("let gameState")
if idx != -1:
    print("GAMESTATE:\n" + content[idx-300:idx+200])
