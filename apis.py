import requests
import textwrap

def get_madrid_weather():
    """Consulta el clima actual de Madrid usando Open-Meteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=40.4165&longitude=-3.7026&current=temperature_2m,weather_code&timezone=Europe%2FMadrid"
        res = requests.get(url, timeout=5).json()
        
        temp = f"{res['current']['temperature_2m']}C"
        code = res['current']['weather_code']
        
        # Códigos WMO básicos
        if code == 0: pronostico = "Despejado"
        elif code in [1, 2, 3]: pronostico = "Nublado"
        elif code in [45, 48]: pronostico = "Niebla"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: pronostico = "Lluvia"
        elif code in [71, 73, 75, 85, 86]: pronostico = "Nieve"
        elif code in [95, 96, 99]: pronostico = "Tormenta"
        else: pronostico = "Variable"
        
        return temp, pronostico
    except Exception:
        return "--C", "Error de red"

def get_fun_fact():
    """Consulta un consejo aleatorio y lo formatea para la pantalla."""
    try:
        url = "https://api.adviceslip.com/advice"
        res = requests.get(url, timeout=5).json()
        advice = res['slip']['advice']
        return textwrap.wrap(advice, width=20) # Cortamos en líneas de 20 caracteres
    except Exception:
        return ["Disfruta tu día,", "Maker."]
