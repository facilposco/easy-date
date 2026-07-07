import sqlite3
import json

db_path = "textgame.db"
video_id = "MNTVs2tDtJg"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Try transcript column first, if fails try raw_text
try:
    cursor.execute("SELECT transcript FROM transcripts WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
except sqlite3.OperationalError:
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()

if row and row[0]:
    with open("transcript_MNTVs2tDtJg.txt", "w", encoding="utf-8") as f:
        f.write(row[0])
    print("Transcript written to transcript_MNTVs2tDtJg.txt")
else:
    print("Row not found.")
conn.close()
