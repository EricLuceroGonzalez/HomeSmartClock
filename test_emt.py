import os
import requests
from dotenv import load_dotenv

# Forzamos la carga del .env
load_dotenv()

CLIENT_ID = os.getenv("EMT_CLIENT_ID")
PASS_KEY  = os.getenv("EMT_PASS_KEY")

print("--- DIAGNÓSTICO EMT MADRID ---")
# Imprimimos solo los primeros 5 caracteres para saber si el .env se lee bien
if CLIENT_ID and PASS_KEY:
    print(f"✅ Llaves encontradas en .env. Client ID empieza por: {CLIENT_ID[:5]}...")
else:
    print("❌ ERROR: No se han encontrado las variables en el archivo .env")
    print("Asegúrate de que el archivo se llama exactamente '.env' y está en esta carpeta.")
    exit()

print("Conectando con el servidor...")
login_url = "https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/"
headers_login = {"X-ClientId": CLIENT_ID, "passKey": PASS_KEY}

try:
    res = requests.get(login_url, headers=headers_login, timeout=5)
    datos = res.json()
    
    print("\n--- RESPUESTA DEL SERVIDOR ---")
    print(f"Código HTTP de red: {res.status_code}")
    print(f"Código interno EMT: {datos.get('code')}")
    print(f"Mensaje EMT: {datos.get('description')}")
    
    if datos.get("code") == "00":
        print("\n🎉 ¡ÉXITO! Las credenciales son válidas.")
    else:
        print("\n⚠️ FALLO: La EMT ha rechazado la conexión.")
        
except Exception as e:
    print(f"Error de red intentando conectar: {e}")
