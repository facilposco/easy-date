import sqlite3

def get_schema():
    conn = sqlite3.connect('textgame.db')
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for table in tables:
        print(f"Table: {table[0]}")
        print(f"Schema: {table[1]}\n")

get_schema()
