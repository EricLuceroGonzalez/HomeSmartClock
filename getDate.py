from datetime import datetime
import os
import json
import textwrap

# --- LECTURA DE EFEMÉRIDES (JSON) ---
def obtener_efemeride():
    hoy = datetime.now().strftime("%m-%d")
    ruta_json = "dates.json"
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
                texto = datos.get(hoy, None)
                if texto:
                    # Envolvemos el texto para que quepa en la pantalla (máximo 20 caracteres por línea)
                    return textwrap.wrap(texto, width=20)
        except Exception:
            pass
    return None