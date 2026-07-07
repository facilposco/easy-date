import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

elements = ["level-progress-display", "rank-display", "calibration-text", "calibration-bar-fill", "chat-area", "user-free-text", "btn-send"]
for elem in elements:
    count = content.count(elem)
    print(f"Element '{elem}': found {count} times")
