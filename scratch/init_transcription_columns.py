import sqlite3

DB_PATH = "textgame.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Agregar columnas si no existen
    columns = [
        ("transcription_text", "TEXT"),
        ("transcription_json", "TEXT")
    ]
    
    # Obtener columnas existentes
    cursor.execute("PRAGMA table_info(reddit_conversations)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    for col_name, col_type in columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE reddit_conversations ADD COLUMN {col_name} {col_type}")
                print(f"Columna '{col_name}' añadida con éxito.")
            except Exception as e:
                print(f"Error al añadir '{col_name}': {e}")
        else:
            print(f"Columna '{col_name}' ya existe.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
