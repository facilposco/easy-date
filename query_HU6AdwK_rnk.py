import sqlite3

def get_transcript():
    try:
        db_path = 'textgame.db'
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'HU6AdwK_rnk'")
        row = cur.fetchone()
        if row:
            with open("transcript_HU6AdwK_rnk.txt", "w", encoding="utf-8") as f:
                f.write(row[0] if row[0] else "")
            print("Transcript written to transcript_HU6AdwK_rnk.txt")
        else:
            print("No transcript found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    get_transcript()
