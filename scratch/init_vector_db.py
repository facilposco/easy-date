import sqlite3
import chromadb
import json

DB_PATH = "textgame.db"
CHROMA_PATH = "./chroma_db"

def init_vector_db():
    print("Inicializando ChromaDB (Motor Vectorial Local)...")
    # Instanciamos el cliente de Chroma apuntando a la carpeta local
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Creamos o cargamos la colección
    collection = chroma_client.get_or_create_collection(
        name="chat_turns_collection",
        metadata={"hnsw:space": "cosine"} # Usar similitud coseno
    )
    
    print("Conectando a SQLite para extraer turnos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, conversation_id, girl_profile_type, user_message, girl_response, outcome, intent_category
        FROM chat_turns
        WHERE user_message IS NOT NULL AND user_message != ''
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No hay turnos en la tabla chat_turns para vectorizar.")
        return
        
    ids = []
    documents = []
    metadatas = []
    
    for row in rows:
        t_id = str(row[0])
        conv_id = row[1]
        profile = row[2] or "desconocida"
        user_msg = row[3]
        girl_resp = row[4]
        outcome = row[5] or "Neutral"
        intent = row[6] or "desconocida"
        
        # El documento principal a vectorizar es el mensaje del usuario
        # para que cuando alguien envíe un mensaje nuevo, busquemos similitudes con estos históricos.
        documents.append(user_msg)
        ids.append(t_id)
        
        # Guardamos la respuesta y la información adicional como metadatos
        metadatas.append({
            "conversation_id": conv_id,
            "girl_profile_type": profile,
            "girl_response": girl_resp,
            "outcome": outcome,
            "intent_category": intent
        })
        
    print(f"Vectorizando e indexando {len(documents)} turnos...")
    
    # ChromaDB (usando el modelo embebido default all-MiniLM-L6-v2) vectoriza
    # automáticamente los documentos si no se proveen embeddings explícitos.
    # Dado el tamaño, agregamos en lotes de 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        b_docs = documents[i:i+batch_size]
        b_ids = ids[i:i+batch_size]
        b_metas = metadatas[i:i+batch_size]
        
        collection.upsert(
            documents=b_docs,
            ids=b_ids,
            metadatas=b_metas
        )
        print(f"Lote {i//batch_size + 1} completado.")
        
    print(f"Proceso finalizado. Total de vectores en la colección: {collection.count()}")
    conn.close()

if __name__ == "__main__":
    init_vector_db()
