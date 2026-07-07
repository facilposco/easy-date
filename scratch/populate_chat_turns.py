import sqlite3
import json

def populate_turns():
    conn = sqlite3.connect('textgame.db')
    cursor = conn.cursor()
    
    # Empty table first just in case
    cursor.execute("DELETE FROM chat_turns")
    
    cursor.execute("SELECT id, girl_profile_type, transcription_json FROM reddit_conversations WHERE transcription_json IS NOT NULL")
    rows = cursor.fetchall()
    
    turns_added = 0
    for row in rows:
        conv_id = row[0]
        profile_type = row[1]
        try:
            data = json.loads(row[2])
        except Exception as e:
            print(f"Error parsing JSON for conv {conv_id}: {e}")
            continue
            
        scoring = 5
        mensajes = []
        
        if isinstance(data, dict):
            scoring = data.get('scoring', 5)
            mensajes = data.get('mensajes', [])
        elif isinstance(data, list):
            mensajes = data
            
        if isinstance(scoring, str):
            try:
                scoring = int(scoring)
            except:
                scoring = 5
                
        outcome = "Positivo" if scoring >= 7 else ("Negativo" if scoring <= 4 else "Neutral")
        
        current_user_msg = ""
        
        for msg in mensajes:
            autor = msg.get('autor', '').lower()
            texto = msg.get('texto', '')
            
            if 'ella' in autor:
                if current_user_msg:
                    # Insert turn
                    cursor.execute('''
                        INSERT INTO chat_turns (conversation_id, girl_profile_type, user_message, girl_response, outcome)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (conv_id, profile_type, current_user_msg, texto, outcome))
                    turns_added += 1
                    current_user_msg = ""
                else:
                    # She texted first or double texted
                    pass
            else:
                # It's 'Él', 'El', or some malformed string for him
                if current_user_msg:
                    current_user_msg += " " + texto
                else:
                    current_user_msg = texto
                    
    conn.commit()
    conn.close()
    print(f"Tabla chat_turns poblada con {turns_added} turnos.")

if __name__ == "__main__":
    populate_turns()
