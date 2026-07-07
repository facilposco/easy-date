import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id='YWck6FeNNRY'")
    row = cursor.fetchone()
    if row and row[0]:
        with open('temp_YWck6FeNNRY.txt', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("Written")
    else:
        print("Not found")

if __name__ == '__main__':
    main()
