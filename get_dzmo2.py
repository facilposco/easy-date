import sqlite3
db = sqlite3.connect('textgame.db')
cursor = db.cursor()
cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'DZMO7su2v5M'")
row = cursor.fetchone()
if row and row[0]:
    with open('transcript_DZMO.txt', 'w', encoding='utf-8') as f:
        f.write(row[0])
    print("SUCCESS")
else:
    print("NOT FOUND OR EMPTY")
