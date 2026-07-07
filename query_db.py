import sqlite3

def query():
    db = sqlite3.connect('textgame.db')
    cursor = db.cursor()
    cursor.execute('SELECT raw_text FROM transcripts WHERE video_id="eHTJ0jSGqIE"')
    row = cursor.fetchone()
    if row:
        with open('transcript.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("Transcript written to transcript.txt")
    else:
        print("Not Found")
    db.close()

if __name__ == '__main__':
    query()
