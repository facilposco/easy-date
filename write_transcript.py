import sqlite3

conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'Z-JRRw0vC6I'")
result = cursor.fetchone()
if result:
    with open('transcript_Z-JRRw0vC6I.txt', 'w', encoding='utf-8') as f:
        f.write(result[0])
    print("Transcript written to transcript_Z-JRRw0vC6I.txt")
else:
    print("Not found")
