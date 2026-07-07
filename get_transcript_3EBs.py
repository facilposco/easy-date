import sqlite3
import sys

db_path = "textgame.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = '3EBs6XYecUc'")
    row = cursor.fetchone()
    if row:
        with open("transcript_3EBs6XYecUc.txt", "w", encoding="utf-8") as f:
            f.write(row[0] if row[0] is not None else "")
        print("Transcript saved successfully to transcript_3EBs6XYecUc.txt")
    else:
        print("Video ID not found in database.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
