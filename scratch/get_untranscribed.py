import sqlite3
import json

DB_PATH = "textgame.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT post_id, local_image_paths 
        FROM reddit_conversations 
        WHERE (transcription_json IS NULL OR transcription_json = '') 
          AND local_image_paths IS NOT NULL 
          AND local_image_paths != '[]'
        LIMIT 10
    """)
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        try:
            paths = json.loads(r[1])
            results.append({
                "post_id": r[0],
                "paths": paths
            })
        except Exception:
            pass
            
    print(json.dumps(results, indent=2))
    conn.close()

if __name__ == "__main__":
    main()
