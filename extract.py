import sqlite3
import sys

def main():
    conn = sqlite3.connect('textgame.db')
    cur = conn.cursor()
    cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'aWVOqkTe1I0';")
    res = cur.fetchone()
    if res:
        print(res[0])
    else:
        print("NOT FOUND")
    
if __name__ == '__main__':
    main()
