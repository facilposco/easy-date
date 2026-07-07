import sqlite3

db_path = 'textgame.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    for t in tables:
        print(f"\nSchema for {t[0]}:")
        cursor.execute(f"PRAGMA table_info({t[0]});")
        columns = cursor.fetchall()
        for c in columns:
            print(c)
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
