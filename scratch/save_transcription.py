import sqlite3
import json
import argparse

DB_PATH = "textgame.db"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post_id", required=True)
    parser.add_argument("--transcription_text", required=True)
    parser.add_argument("--transcription_json", required=True)
    parser.add_argument("--girl_profile_type", required=True)
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Validar si es JSON válido
        json.loads(args.transcription_json)
        
        cursor.execute("""
            UPDATE reddit_conversations 
            SET transcription_text = ?, transcription_json = ?, girl_profile_type = ? 
            WHERE post_id = ?
        """, (args.transcription_text, args.transcription_json, args.girl_profile_type, args.post_id))
        conn.commit()
        print(f"Post {args.post_id} transcrito y clasificado como '{args.girl_profile_type}' guardado con éxito.")
    except Exception as e:
        print(f"Error al guardar: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
