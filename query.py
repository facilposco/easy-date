import sqlite3

db = sqlite3.connect('textgame.db')
c = db.cursor()
c.execute("SELECT message FROM transcripts WHERE video_id='eHTJ0jSGqIE'")
res = c.fetchone()
if res and res[0]:
    print(res[0][:2000])
else:
    print("NO_MESSAGE_COLUMN_DATA")
