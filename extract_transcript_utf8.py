import sqlite3

def get_transcript():
    try:
        conn = sqlite3.connect('textgame.db')
        cursor = conn.cursor()
        cursor.execute("SELECT raw_text FROM transcripts WHERE video_id='mByptEwm4VM'")
        row = cursor.fetchone()
        with open('transcript_mByptEwm4VM_utf8.txt', 'w', encoding='utf-8') as f:
            if row:
                f.write(row[0] if row[0] else 'NULL')
            else:
                f.write("NOT_FOUND")
    except Exception as e:
        with open('transcript_mByptEwm4VM_utf8.txt', 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    get_transcript()
