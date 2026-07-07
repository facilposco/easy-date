import os
import json
import sqlite3

PARSED_DIR = "parsed_cases"
REDDIT_DIR = "reddit_cases"

def main():
    stats = {
        "YouTube (parsed_cases)": {10: 0, 9: 0, 8: 0, 7: 0, 6: 0, "otros": 0},
        "Reddit (reddit_cases)": {10: 0, 9: 0, 8: 0, 7: 0, 6: 0, "otros": 0},
        "Total": {10: 0, 9: 0, 8: 0, 7: 0, 6: 0, "otros": 0}
    }
    
    # YouTube (parsed_cases)
    if os.path.exists(PARSED_DIR):
        for fname in os.listdir(PARSED_DIR):
            if fname.endswith(".json") and not fname.startswith("translate_"):
                try:
                    with open(os.path.join(PARSED_DIR, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        score_val = data.get("scoring")
                        if score_val is not None:
                            val = int(float(score_val))
                            if val in [10, 9, 8, 7, 6]:
                                stats["YouTube (parsed_cases)"][val] += 1
                                stats["Total"][val] += 1
                            else:
                                stats["YouTube (parsed_cases)"]["otros"] += 1
                                stats["Total"]["otros"] += 1
                except Exception as e:
                    pass

    # Reddit (reddit_cases)
    if os.path.exists(REDDIT_DIR):
        for fname in os.listdir(REDDIT_DIR):
            if fname.endswith(".json") and not fname.startswith("translate_"):
                try:
                    with open(os.path.join(REDDIT_DIR, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        score_val = data.get("scoring")
                        if score_val is not None:
                            val = int(float(score_val))
                            if val in [10, 9, 8, 7, 6]:
                                stats["Reddit (reddit_cases)"][val] += 1
                                stats["Total"][val] += 1
                            else:
                                stats["Reddit (reddit_cases)"]["otros"] += 1
                                stats["Total"]["otros"] += 1
                except Exception as e:
                    pass

    print("\n| Categoría | Score 10 | Score 9 | Score 8 | Score 7 | Score 6 | Otros/Fails | Total |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for category in ["YouTube (parsed_cases)", "Reddit (reddit_cases)", "Total"]:
        row = stats[category]
        total_row = sum(row[k] for k in [10, 9, 8, 7, 6, "otros"])
        print(f"| {category} | {row[10]} | {row[9]} | {row[8]} | {row[7]} | {row[6]} | {row['otros']} | {total_row} |")

if __name__ == "__main__":
    main()
