import os
import json

PARSED_DIR = "parsed_cases"
REDDIT_DIR = "reddit_cases"

def load_all():
    cases = []
    
    if os.path.exists(PARSED_DIR):
        for f in os.listdir(PARSED_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(PARSED_DIR, f), "r", encoding="utf-8") as file:
                        data = json.load(file)
                        cases.append({
                            "source": "youtube",
                            "id": f,
                            "title": data.get("video_id", f),
                            "scoring": data.get("scoring", 0),
                            "justificacion": data.get("justificacion_scoring", ""),
                            "data": data
                        })
                except Exception as e:
                    print(f"Error loading {f}: {e}")
                    
    if os.path.exists(REDDIT_DIR):
        for f in os.listdir(REDDIT_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(REDDIT_DIR, f), "r", encoding="utf-8") as file:
                        data = json.load(file)
                        cases.append({
                            "source": "reddit",
                            "id": f,
                            "title": data.get("title", f),
                            "scoring": data.get("scoring", 0),
                            "justificacion": data.get("justificacion_scoring", ""),
                            "data": data
                        })
                except Exception as e:
                    print(f"Error loading {f}: {e}")
                    
    print(f"Loaded {len(cases)} cases total.")
    return cases

if __name__ == "__main__":
    cases = load_all()
    # Print a summary table of the cases
    print(f"{'Source':<8} | {'ID':<20} | {'Score':<5} | {'Steps Count'}")
    print("-" * 50)
    for c in sorted(cases, key=lambda x: x["scoring"], reverse=True):
        # Count steps/messages
        steps_count = 0
        if c["source"] == "youtube":
            for fase in c["data"].get("fases", []):
                steps_count += len(fase.get("mensajes", []))
        else:
            steps_count = len(c["data"].get("mensajes", []))
        print(f"{c['source']:<8} | {c['id']:<20} | {c['scoring']:<5} | {steps_count} messages")
