import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key1 = os.getenv("GEMINI_API_KEY_1")
if not key1:
    print("No key found!")
    exit(1)

genai.configure(api_key=key1)

print("Listando modelos disponibles...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Error:", e)
