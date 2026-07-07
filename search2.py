import sqlite3
import re

db = sqlite3.connect('textgame.db')
c = db.cursor()
c.execute('SELECT raw_text FROM transcripts WHERE video_id="eHTJ0jSGqIE"')
row = c.fetchone()
if row:
    text = row[0]
    # find occurrences of "number" or "date" or "success" or "come over"
    # we just print the index and 500 chars around it
    for match in re.finditer(r'(number|date|number close|come over|succeed|hook up)', text, re.IGNORECASE):
        start = max(0, match.start() - 300)
        end = min(len(text), match.end() + 300)
        print("------- MATCH -------")
        print(text[start:end])
else:
    print("NOT FOUND")
