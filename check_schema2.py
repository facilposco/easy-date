import sqlite3
db = sqlite3.connect('textgame.db')
cursor = db.cursor()
cursor.execute("PRAGMA table_info(transcripts)")
print("transcripts table:", cursor.fetchall())
cursor.execute("PRAGMA table_info(videos)")
print("videos table:", cursor.fetchall())
