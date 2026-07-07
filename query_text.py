import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = 'G01G2HzjpFQ';")
    result = cursor.fetchone()
    if result:
        with open('transcript.txt', 'w', encoding='utf-8') as f:
            f.write(result[0] or "")
        print("Transcript saved to transcript.txt")
    else:
        print("Not found")

if __name__ == '__main__':
    main()
