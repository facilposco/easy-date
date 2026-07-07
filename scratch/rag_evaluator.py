import chromadb
import google.generativeai as genai
import os
import json

CHROMA_PATH = "./chroma_db"

def evaluate_free_text(user_input, girl_profile, context_history=""):
    print(f"Evaluando input: '{user_input}' para perfil: '{girl_profile}'")
    
    # 1. Recuperar contexto semántico de ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        collection = chroma_client.get_collection(name="chat_turns_collection")
    except Exception as e:
        print("La colección ChromaDB no existe aún. Ejecuta init_vector_db.py primero.")
        return None
        
    # Búsqueda semántica usando el modelo interno de Chroma
    results = collection.query(
        query_texts=[user_input],
        n_results=5,
        # Opcional: filtrar por perfil
        # where={"girl_profile_type": girl_profile}
    )
    
    # Construir el bloque RAG de ejemplos
    rag_context = ""
    if results['documents'] and len(results['documents'][0]) > 0:
        rag_context += "EJEMPLOS HISTÓRICOS SIMILARES (Referencia de cómo suelen terminar estas interacciones):\n"
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        for i in range(len(docs)):
            rag_context += f"- Interacción {i+1}:\n"
            rag_context += f"  Usuario dijo: \"{docs[i]}\"\n"
            rag_context += f"  La chica ({metas[i]['girl_profile_type']}) respondió: \"{metas[i]['girl_response']}\"\n"
            rag_context += f"  Resultado Final: {metas[i]['outcome']} (Intención: {metas[i]['intent_category']})\n\n"
    else:
        rag_context += "No se encontraron interacciones similares.\n"
        
    # 2. Configurar Gemini 3.1 Pro para la evaluación
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    
    # Usaremos gemini-1.5-pro o el modelo que esté disponible (idealmente Pro para lógica compleja)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    prompt = f"""
Eres un simulador avanzado de dinámicas sociales y citas, actuando como el cerebro detrás de una chica virtual llamada Natalia (Perfil: {girl_profile}).
El usuario está intentando seducirte y calibrar la conversación. Su entrada libre es: "{user_input}".

{rag_context}
Historia reciente del chat:
{context_history}

Tu tarea:
1. Analiza el 'user_input' basándote en los Ejemplos Históricos Similares provistos arriba. Compara si este tipo de comentario suele tener un resultado Positivo, Negativo o Neutral.
2. Evalúa la calibración del usuario (es necesitado? es atractivo? es aburrido?).
3. Genera la respuesta exacta de Natalia a este mensaje, manteniendo su personalidad ({girl_profile}).
4. Asigna un impacto en la 'inversión' (puntaje de vida) del -25 al +20.

Devuelve tu respuesta ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{{
    "analysis_feedback": "Tu análisis breve para el coach",
    "her_response": "La respuesta de Natalia en texto",
    "investment_impact": 15,
    "outcome_category": "Positivo" 
}}
"""
    print("Enviando prompt RAG a Gemini Pro...")
    try:
        response = model.generate_content(prompt)
        # Extraer el JSON
        text = response.text
        # Limpiar markdown de json si lo hay
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text.strip())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except Exception as e:
        print(f"Error evaluando con Gemini: {e}")
        return None

if __name__ == "__main__":
    # Test rápido
    evaluate_free_text(
        user_input="Oye, eres súper hermosa, me encantaría llevarte a un restaurante carísimo hoy mismo",
        girl_profile="defensiva"
    )
