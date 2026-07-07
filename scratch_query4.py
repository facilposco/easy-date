import sqlite3

try:
    db = sqlite3.connect('textgame.db')
    cur = db.cursor()
    cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'XaSn9eHHyX0'")
    res = cur.fetchone()
    if res:
        with open("transcript_XaSn9eHHyX0.txt", "w", encoding="utf-8") as f:
            f.write(res[0])
        print("Done")
    else:
        print("NOT_FOUND")
except Exception as e:
    print("ERROR:", e)
