import sqlite3
import json
import os

DB_PATH = "textgame.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de conversaciones principales
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reddit_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT UNIQUE,
        title TEXT,
        url TEXT,
        score INTEGER,
        post_type TEXT,
        body_text TEXT,
        image_urls TEXT,
        local_image_paths TEXT,
        created_utc INTEGER
    );
    """)
    
    # Virtual table de búsqueda FTS5 para emular base de datos vectorial/semántica (similar a ChromaDB)
    # FTS5 permite búsquedas avanzadas por relevancia con MATCH y ranking BM25
    try:
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS reddit_conversations_search USING fts5(
            title,
            body_text,
            content='reddit_conversations',
            content_rowid='id'
        );
        """)
        # Triggers para mantener actualizada la tabla de búsqueda
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tbl_ai AFTER INSERT ON reddit_conversations BEGIN
          INSERT INTO reddit_conversations_search(rowid, title, body_text) VALUES (new.id, new.title, new.body_text);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tbl_ad AFTER DELETE ON reddit_conversations BEGIN
          INSERT INTO reddit_conversations_search(reddit_conversations_search, rowid, title, body_text) VALUES('delete', old.id, old.title, old.body_text);
        END;
        """)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS tbl_au AFTER UPDATE ON reddit_conversations BEGIN
          INSERT INTO reddit_conversations_search(reddit_conversations_search, rowid, title, body_text) VALUES('delete', old.id, old.title, old.body_text);
          INSERT INTO reddit_conversations_search(rowid, title, body_text) VALUES (new.id, new.title, new.body_text);
        END;
        """)
    except sqlite3.OperationalError as e:
        print("FTS5 no está disponible o ya está configurado:", e)
        
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

def insert_conversation(post_id, title, url, score, post_type, body_text, image_urls, local_image_paths, created_utc):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Guardar listas serializadas
    urls_str = json.dumps(image_urls)
    paths_str = json.dumps(local_image_paths)
    
    try:
        cursor.execute("""
        INSERT INTO reddit_conversations 
        (post_id, title, url, score, post_type, body_text, image_urls, local_image_paths, created_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            title=excluded.title,
            score=excluded.score,
            body_text=excluded.body_text,
            image_urls=excluded.image_urls,
            local_image_paths=excluded.local_image_paths;
        """, (post_id, title, url, score, post_type, body_text, urls_str, paths_str, created_utc))
        conn.commit()
        success = True
    except Exception as e:
        print("Error insertando conversación:", e)
        success = False
    finally:
        conn.close()
    return success

def search_conversations(query, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Búsqueda usando FTS5 ordenando por relevancia BM25
    try:
        cursor.execute("""
        SELECT rc.id, rc.post_id, rc.title, rc.post_type, rc.body_text, rc.score, rc.local_image_paths 
        FROM reddit_conversations rc
        JOIN reddit_conversations_search rcs ON rc.id = rcs.rowid
        WHERE reddit_conversations_search MATCH ?
        ORDER BY rank
        LIMIT ?;
        """, (query, limit))
        results = cursor.fetchall()
    except Exception as e:
        print("Error en búsqueda FTS5 (cayendo a LIKE estándar):", e)
        # Fallback si MATCH falla por sintaxis
        cursor.execute("""
        SELECT id, post_id, title, post_type, body_text, score, local_image_paths
        FROM reddit_conversations
        WHERE title LIKE ? OR body_text LIKE ?
        ORDER BY score DESC
        LIMIT ?;
        """, (f"%{query}%", f"%{query}%", limit))
        results = cursor.fetchall()
    finally:
        conn.close()
        
    formatted = []
    for r in results:
        formatted.append({
            "id": r[0],
            "post_id": r[1],
            "title": r[2],
            "post_type": r[3],
            "body_text": r[4],
            "score": r[5],
            "local_image_paths": json.loads(r[6]) if r[6] else []
        })
    return formatted

if __name__ == "__main__":
    init_db()
