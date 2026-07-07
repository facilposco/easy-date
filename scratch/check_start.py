import json

with open("backend/levels_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

for lvl_id, data in config.items():
    print(f"Level {lvl_id} ({data['profile']}):")
    history = data["chat_history"]
    if history:
        print(f"  First turn keys: {history[0].keys()}")
        print(f"  First turn data: {history[0]}")
    else:
        print("  Empty history!")
