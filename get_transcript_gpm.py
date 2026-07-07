import sqlite3

def get_transcript():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id='gpmQMd-wfgk'")
    row = cursor.fetchone()
    if row:
        with open('temp_gpm.txt', 'w', encoding='utf-8') as f:
            f.write(row[0] if row[0] is not None else "")
        print("Transcript saved to temp_gpm.txt")
    else:
        print("Not found")

get_transcript()
