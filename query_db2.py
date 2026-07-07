import sqlite3

conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
try:
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'cIoiNZC1K7s'")
    row = cursor.fetchone()
    if row:
        with open('transcript_cIoiNZC1K7s.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("Transcript saved to transcript_cIoiNZC1K7s.txt")
    else:
        print("Not found in transcripts table.")
except Exception as e:
    print("Error:", e)
conn.close()
