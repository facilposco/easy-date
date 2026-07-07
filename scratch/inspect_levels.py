import json
import re

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

# Match the gameData variable declaration
match = re.search(r"const gameData\s*=\s*(\{.*?\});", content)
if match:
    gd_json = match.group(1)
    gd = json.loads(gd_json)
    print("Levels in gameData in HTML:")
    for idx, lvl in enumerate(gd.get("levels", [])):
        print(f"  Level {idx+1}: {lvl.get('girl_name')} (ID: {lvl.get('level_id') or lvl.get('post_id')})")
else:
    print("Could not find const gameData in HTML!")
