import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(transcripts)")
    rows = c.fetchall()
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    main()
