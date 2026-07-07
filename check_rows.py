import sqlite3
conn = sqlite3.connect('textgame.db')
cursor = conn.cursor()
cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'fGGmXL2vmos'")
rows = cursor.fetchall()
print(f"Number of rows: {len(rows)}")
for i, r in enumerate(rows):
    print(f"Row {i} length: {len(r[0])}")
