import sqlite3

db_path = 'textgame.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = '8R_BIDyCoRM'")
    row = cursor.fetchone()
    if row and row[0]:
        print("8R_BIDyCoRM transcript found! Length:", len(row[0]))
        with open('transcript_8R.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
    else:
        print("Not found or null")
    
except Exception as e:
    print("Error:", e)
