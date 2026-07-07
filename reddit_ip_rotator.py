import os
import random
import string
import tls_client
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("PROXY_HOST")
port = os.getenv("PROXY_PORT")
user = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")

print("Iniciando rotacion de IPs con DataImpulse y TLS-Client...")

for i in range(5):
    # Generar un ID de sesion aleatorio para forzar una IP nueva
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    
    # Diferentes proveedores usan distinta sintaxis. Las 3 mas comunes:
    formats = [
        f"{user}_session-{session_id}",
        f"{user}__session__{session_id}",
        f"{user}-session-{session_id}"
    ]
    
    for user_fmt in formats:
        proxy = f"http://{user_fmt}:{password}@{host}:{port}"
        
        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        
        print(f"Probando IP rotada con formato: {user_fmt}")
        try:
            response = session.get(
                "https://www.reddit.com/r/Tinder/top.json?limit=1",
                proxy=proxy,
                timeout_seconds=10
            )
            print(f"Resultado: {response.status_code}")
            if response.status_code == 200:
                print("¡IP DESBLOQUEADA ENCONTRADA!")
                exit(0)
            elif response.status_code == 403:
                # Comprobar si al menos cargo HTML o WAF
                if "blocked by network security" in response.text.lower():
                    pass # WAF estricto
        except Exception as e:
            pass
