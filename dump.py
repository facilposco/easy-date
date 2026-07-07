import sqlite3
import json

db_path = r'C:\desarrollos\antigravity\text game youtube estudio ejemplos\textgame.db'
out_path = r'C:\desarrollos\antigravity\text game youtube estudio ejemplos\output_transcription.json'

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT video_id, transcript_text FROM transcriptions WHERE video_id = 'QvOMpdluaoE'")
    rows = cursor.fetchall()
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump([{"video_id": row[0], "text": row[1]} for row in rows], f, indent=4, ensure_ascii=False)
