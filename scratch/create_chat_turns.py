import sqlite3

def init_db():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    
    # Create chat_turns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            girl_profile_type TEXT,
            user_message TEXT,
            girl_response TEXT,
            outcome TEXT,
            intent_category TEXT,
            FOREIGN KEY(conversation_id) REFERENCES reddit_conversations(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Tabla chat_turns creada correctamente.")

if __name__ == "__main__":
    init_db()
