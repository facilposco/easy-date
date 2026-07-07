import sqlite3
import json

DB_PATH = "textgame.db"

def inspect_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print("Tables in DB:", tables)
    
    for t in tables:
        print(f"\nSchema of {t}:")
        cursor.execute(f"PRAGMA table_info({t})")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
            
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  Total rows: {cursor.fetchone()[0]}")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
