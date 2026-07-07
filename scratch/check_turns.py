import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("backend/levels_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

for lvl_id, data in config.items():
    print(f"\nLevel {lvl_id} ({data['profile']}):")
    history = data["chat_history"]
    for idx, turn in enumerate(history[:5]):
        print(f"  Turn {idx+1}: {turn['sender']}: {turn['text']}")
