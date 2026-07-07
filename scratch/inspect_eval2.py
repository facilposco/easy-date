import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("async function evaluateSelection")
if idx != -1:
    end = content.find("function showCoachModal", idx)
    print("EVALUATE SELECTION:")
    print(content[idx:end])
