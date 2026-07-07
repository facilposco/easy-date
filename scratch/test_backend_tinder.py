import requests
import json

url = "http://127.0.0.1:8000/api/evaluate"
payload = {
    "level": 1,
    "history": [],
    "user_message": "hola, ¿cómo estás?"
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload)
    print("STATUS:", response.status_code)
    print("RESPONSE:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
