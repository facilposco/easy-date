import sqlite3

conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='transcripts';")
print(cursor.fetchone()[0])
