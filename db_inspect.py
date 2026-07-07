import sqlite3
import sys

conn = sqlite3.connect('textgame.db')
cur = conn.cursor()

try:
    cur.execute("SELECT raw_text FROM transcripts WHERE video_id = '8R_BIDyCoRM'")
    row = cur.fetchone()
    if row:
        with open('transcript_8R_BIDyCoRM.txt', 'w', encoding='utf-8') as f:
            f.write(row[0] if row[0] is not None else '')
        print("Transcript saved successfully.")
    else:
        print("Record not found.")
except Exception as e:
    print("Error:", e)
    
conn.close()
