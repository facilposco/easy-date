import sqlite3

try:
    db = sqlite3.connect('textgame.db')
    cur = db.cursor()
    cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'XaSn9eHHyX0'")
    res = cur.fetchone()
    if res:
        print("---BEGIN TRANSCRIPT---")
        print(res[0])
        print("---END TRANSCRIPT---")
    else:
        print("NOT_FOUND")
except Exception as e:
    print("ERROR:", e)
