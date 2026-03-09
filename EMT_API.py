import os
import requests
from dotenv import load_dotenv

# Cargar las variables del archivo .env al vuelo
load_dotenv()


def get_emt_bus(stop_id="5036"):
    """Consulta los próximos buses de la EMT usando MobilityLabs y .env."""

    # Extraemos las llaves secretas del entorno
    CLIENT_ID = os.getenv("EMT_CLIENT_ID")
    PASS_KEY = os.getenv("EMT_PASS_KEY")

    if not CLIENT_ID or not PASS_KEY:
        return ["Faltan llaves", "en el .env"]

    try:
        # 1. Iniciar sesión
        login_url = "https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/"
        headers_login = {"X-ClientId": CLIENT_ID, "passKey": PASS_KEY}
        res_login = requests.get(login_url, headers=headers_login, timeout=5).json()

        if res_login.get("code") not in ["00", "01", "02"]:
            return ["Error de", "credenciales"]

        token = res_login["data"][0]["accessToken"]

        # 2. Consultar parada
        stop_url = f"https://openapi.emtmadrid.es/v2/transport/busemtmad/stops/{stop_id}/arrives/"
        headers_stop = {"accessToken": token}
        payload = {
            "cultureInfo": "ES",
            "Text_StopRequired_YN": "N",
            "Text_EstimationsRequired_YN": "Y",
            "Text_IncidencesRequired_YN": "N",
            "DateTime_Referenced_Incidencies_YYYYMMDD": "20240101",  # Fecha fija según doc de EMT
        }

        res_stop = requests.post(
            stop_url, headers=headers_stop, json=payload, timeout=5
        ).json()
        buses = res_stop["data"][0].get("Arrive", [])

        if not buses:
            return ["No hay buses", "cerca"]

        buses_ordenados = sorted(buses, key=lambda x: x["estimateArrive"])
        resultados = []

        for bus in buses_ordenados[:3]:
            linea = bus["line"]
            minutos = bus["estimateArrive"] // 60

            if minutos <= 0:
                tiempo_str = "Llegando"
            elif minutos > 45:
                tiempo_str = "+45 min"
            else:
                tiempo_str = f"{minutos} min"

            resultados.append(f"Linea {linea}: {tiempo_str}")

        return resultados

    except Exception:
        return ["Error red", "EMT Madrid"]
