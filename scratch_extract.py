import sqlite3

def get_transcript():
    conn = sqlite3.connect('textgame.db')
    cur = conn.cursor()
    cur.execute("SELECT raw_text FROM transcripts WHERE video_id = 'F16tI29Jtb4'")
    row = cur.fetchone()
    
    if row:
        with open('transcript_output.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("Transcript written to transcript_output.txt")
    else:
        print("NOT FOUND")

if __name__ == "__main__":
    get_transcript()
