import os
import json

PARSED_DIR = "parsed_cases"
REDDIT_DIR = "reddit_cases"

def extract_flow(filepath, is_youtube=True):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    messages = []
    if is_youtube:
        for fase in data.get("fases", []):
            for m in fase.get("mensajes", []):
                messages.append({
                    "autor": "Él" if m.get("autor", "").lower() in ["el", "él"] else "Ella",
                    "texto": m.get("texto", "")
                })
    else:
        for m in data.get("mensajes", []):
            messages.append({
                "autor": "Él" if m.get("autor", "").lower() in ["el", "él"] else "Ella",
                "texto": m.get("texto", "")
            })
            
    # Clean contiguous duplicates (same author sending multiple messages back to back)
    cleaned = []
    for m in messages:
        if not cleaned:
            cleaned.append(m)
        else:
            if cleaned[-1]["autor"] == m["autor"]:
                cleaned[-1]["texto"] += " \n " + m["texto"]
            else:
                cleaned.append(m)
    return cleaned

def main():
    for folder, is_yt in [(PARSED_DIR, True), (REDDIT_DIR, False)]:
        if not os.path.exists(folder):
            continue
        print(f"\n===== FILES IN {folder} =====")
        for fname in os.listdir(folder):
            if fname.endswith(".json") and not fname.startswith("translate_"):
                flow = extract_flow(os.path.join(folder, fname), is_yt)
                if len(flow) >= 10:
                    print(f"File: {fname} | alternations: {len(flow)}")
                    # print first 4 messages
                    for m in flow[:4]:
                        print(f"  {m['autor']}: {m['texto'][:100]}")
                    print("-" * 20)

if __name__ == "__main__":
    main()
