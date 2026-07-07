import sqlite3
db = sqlite3.connect('textgame.db')
cursor = db.cursor()
cursor.execute("SELECT transcript FROM transcripts WHERE video_id = 'DZMO7su2v5M'")
row = cursor.fetchone()
if row:
    with open('transcript_DZMO_debug.txt', 'w', encoding='utf-8') as f:
        f.write(row[0])
    print("SUCCESS")
else:
    print("NOT FOUND transcripts table")
    cursor.execute("SELECT transcript FROM videos WHERE video_id = 'DZMO7su2v5M'")
    row = cursor.fetchone()
    if row:
        with open('transcript_DZMO_debug.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("SUCCESS videos table")
    else:
        print("NOT FOUND videos table")
