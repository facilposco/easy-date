import sqlite3

db_path = "textgame.db"
video_id = "jxDPEtG39mE"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT raw_text FROM transcripts WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    
    if row:
        with open("transcript_jxDPEtG39mE.txt", "w", encoding="utf-8") as f:
            f.write(row[0])
        print("Transcript written to transcript_jxDPEtG39mE.txt")
    else:
        print("Row not found.")
        
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
