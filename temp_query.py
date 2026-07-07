import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    c = conn.cursor()
    c.execute("SELECT raw_text FROM transcripts WHERE video_id='Lss_cULdgPs'")
    row = c.fetchone()
    if row:
        print(row[0])
    else:
        print("NOT_FOUND")
    conn.close()

if __name__ == "__main__":
    main()
