import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transcripts);")
    results = cursor.fetchall()
    for row in results:
        print(row)

if __name__ == '__main__':
    main()
