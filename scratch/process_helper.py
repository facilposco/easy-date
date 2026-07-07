import os
import json
import subprocess
import sys
import glob
import re

DB_PATH = "textgame.db"

def get_next_multi_index():
    files = glob.glob("reddit_cases/multi_*.json")
    max_idx = 3 # default start from 3
    for f in files:
        match = re.search(r"multi_(\d+)\.json", f)
        if match:
            idx = int(match.group(1))
            if idx > max_idx:
                max_idx = idx
    return max_idx + 1

def save_case(post_id, title_es, resumen_estrategico, scoring, justificacion_scoring, mensajes, girl_profile_type, transcription_text):
    # Determine index
    idx = get_next_multi_index()
    json_filename = f"reddit_cases/multi_{idx}.json"
    
    # Construct the JSON object
    data = {
        "titulo": title_es,
        "resumen_estrategico": resumen_estrategico,
        "scoring": scoring,
        "justificacion_scoring": justificacion_scoring,
        "mensajes": mensajes
    }
    
    # Write the JSON file
    os.makedirs("reddit_cases", exist_ok=True)
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {json_filename}")
    
    # Run the save_transcription.py command
    json_str = json.dumps(data, ensure_ascii=False)
    cmd = [
        sys.executable,
        "scratch/save_transcription.py",
        "--post_id", post_id,
        "--transcription_text", transcription_text,
        "--transcription_json", json_str,
        "--girl_profile_type", girl_profile_type
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if res.returncode == 0:
        print(f"Database updated successfully for post_id: {post_id}")
        if res.stdout:
            print(res.stdout.strip())
    else:
        print(f"Error updating database for post_id: {post_id}")
        if res.stderr:
            print(res.stderr.strip())
        if res.stdout:
            print(res.stdout.strip())

if __name__ == "__main__":
    # Test script if run directly
    print("Next multi index is:", get_next_multi_index())
