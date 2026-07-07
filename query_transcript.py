import sqlite3

db = sqlite3.connect('textgame.db')
cursor = db.cursor()
cursor.execute("SELECT * FROM transcripts WHERE video_id = '0IUoTwkmRKs';")
row = cursor.fetchone()
if row:
    with open('transcript_0IUoTwkmRKs.txt', 'w', encoding='utf-8') as f:
        f.write(str(row))
else:
    with open('transcript_0IUoTwkmRKs.txt', 'w', encoding='utf-8') as f:
        f.write("Not found")
