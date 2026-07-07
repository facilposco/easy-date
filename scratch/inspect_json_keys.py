import json

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    for line in f:
        if "const gameData =" in line:
            # extract the JSON part
            start_idx = line.find("{")
            end_idx = line.rfind("}") + 1
            gd_json = line[start_idx:end_idx]
            gd = json.loads(gd_json)
            print("Structure keys:", gd.keys())
            print("First level keys:", gd["levels"][0].keys())
            print("First level steps keys:", gd["levels"][0]["steps"][0].keys())
            break
