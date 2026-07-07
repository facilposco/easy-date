import sqlite3

def main():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    results = cursor.fetchall()
    for row in results:
        print(row[0])

if __name__ == '__main__':
    main()
