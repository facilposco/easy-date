import sqlite3
import json
import sys

db_path = "textgame.db"
video_id = "jxDPEtG39mE"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    table_name = "transcripts"
    
    cursor.execute(f"PRAGMA table_info({table_name});")
    print("Columns:", cursor.fetchall())
    
    cursor.execute(f"SELECT * FROM {table_name} WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    
    if row:
        print("Found row!")
        for i, col in enumerate(row):
            val = str(col)
            print(f"Col {i}: {val[:500]}")
    else:
        print("Row not found.")
        
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
