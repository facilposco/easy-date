import requests
import json

def test_api():
    url = "http://localhost:8000/api/evaluate"
    payload = {
        "level": 1,
        "history": [
            {"role": "assistant", "content": "Hola, ¿cómo estás?"}
        ],
        "user_message": "Hola, te vi el otro día y me pareciste simpática."
    }
    
    print("Enviando petición de prueba al backend...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n--- EVALUACIÓN DEL COACH MAXIMUS ---")
            print(data.get("evaluation"))
            print("\n--- NUEVO HISTORIAL ---")
            print(json.dumps(data.get("new_history"), indent=2))
        else:
            print("Error en el servidor:", response.text)
    except Exception as e:
        print("Error de conexión:", e)

if __name__ == '__main__':
    test_api()
