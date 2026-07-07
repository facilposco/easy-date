import sqlite3

conn = sqlite3.connect('textgame.db')
cur = conn.cursor()
cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'fGGmXL2vmos'")
row = cur.fetchone()
if row:
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        f.write(row[0])
    print("Transcript saved to transcript.txt")
else:
    print("No transcript found for video_id 'fGGmXL2vmos'")
