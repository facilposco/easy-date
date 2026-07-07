import sqlite3
import json
conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(transcripts);")
print("Schema:", cursor.fetchall())
cursor.execute("SELECT * FROM transcripts WHERE video_id = 'Z-JRRw0vC6I'")
result = cursor.fetchone()
if result:
    print(result)
else:
    print("Not found")
