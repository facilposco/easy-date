import sqlite3

try:
    db = sqlite3.connect('textgame.db')
    cur = db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables:", tables)
    if tables:
        for table in tables:
            cur.execute(f"PRAGMA table_info({table[0]})")
            print(f"Schema of {table[0]}:", cur.fetchall())
except Exception as e:
    print("ERROR:", e)
