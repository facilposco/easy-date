import sqlite3
import json

db_path = r'C:\desarrollos\antigravity\text game youtube estudio ejemplos\textgame.db'
out_path = r'C:\desarrollos\antigravity\text game youtube estudio ejemplos\schema.json'

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema = {}
    for t in tables:
        t_name = t[0]
        cursor.execute(f"PRAGMA table_info({t_name});")
        schema[t_name] = cursor.fetchall()
        
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=4)
