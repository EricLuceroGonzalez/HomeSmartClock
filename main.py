import time
import threading
import random
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import adafruit_dht
import adafruit_as7341
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import apis
import json
import textwrap

# --- 1. LECTURA DE EFEMÉRIDES (JSON) ---
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

# --- 2. INICIALIZAR HARDWARE ---
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D23)
reset_pin = digitalio.DigitalInOut(board.D24)
oled = adafruit_ssd1306.SSD1306_SPI(128, 64, spi, dc_pin, reset_pin, cs_pin)

try:
    dht_device = adafruit_dht.DHT11(board.D4)
except: pass

try:
    i2c = board.I2C()
    sensor_luz = adafruit_as7341.AS7341(i2c)
except:
    sensor_luz = None

# --- 3. CARGA DE FUENTES ---
# Se han instalado previamente con: sudo apt-get install fonts-dejavu-core -y
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
icon_path = "fa-solid-900.ttf" 

try:
    font_titulo = ImageFont.truetype(font_path, 12)  
    font_datos  = ImageFont.truetype(font_path, 26)  
    font_hora   = ImageFont.truetype(font_path, 42)  
    font_texto  = ImageFont.truetype(font_path, 11)
    font_iconos = ImageFont.truetype(icon_path, 20)
except:
    font_titulo = font_datos = font_hora = font_texto = font_iconos = ImageFont.load_default()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# --- 4. VARIABLES GLOBALES ---
ultima_temp_int = "--"
ultima_hum_int = "--"
ultimo_check_dht = 0

api_temp_ext = "--"
api_pronostico = "Cargando..."
api_fact_lineas = ["Buscando", "datos..."]

# Control de Carrusel
estado_actual = 0  
ultimo_cambio = time.time()
duracion_actual = 10 # Tiempo dinámico de la diapositiva actual

# Modo Noche y Anti Burn-in
offset_x, offset_y = 0, 0
ultimo_shift = time.time()
oscuridad_consecutiva = 0
UMBRAL_OSCURIDAD = 80 

# --- 5. HILO DE INTERNET ---
def actualizar_internet():
    global api_temp_ext, api_pronostico, api_fact_lineas
    while True:
        api_temp_ext, api_pronostico = apis.get_madrid_weather()
        api_fact_lineas = apis.get_fun_fact()
        time.sleep(120)

threading.Thread(target=actualizar_internet, daemon=True).start()

# --- 6. BUCLE PRINCIPAL ---
print("Smart Clock iniciado. Presiona Ctrl+C para salir.")

while True:
    tiempo_actual = time.time()

    # A. PIXEL SHIFTING
    if tiempo_actual - ultimo_shift > 60:
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-1, 1)
        ultimo_shift = tiempo_actual

    # B. MODO SUEÑO PROFUNDO
    if sensor_luz:
        try:
            luz = sensor_luz.channel_555nm + sensor_luz.channel_590nm
            if luz < UMBRAL_OSCURIDAD:
                oscuridad_consecutiva += 1
            else:
                oscuridad_consecutiva = 0
        except: pass

    if oscuridad_consecutiva > 10: 
        # Apagado total de la pantalla
        draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
        oled.image(image)
        oled.show()
        time.sleep(2.0) # Duerme el procesador 2 segundos enteros
        ultimo_cambio = time.time() # Resetea el carrusel para cuando despierte
        continue 

    # C. LECTURA DHT11
    if (tiempo_actual - ultimo_check_dht) > 3.0:
        try:
            t = dht_device.temperature
            h = dht_device.humidity
            if t is not None and h is not None:
                ultima_temp_int = f"{t:.1f}C"
                ultima_hum_int = f"{h}%"
        except: pass  
        ultimo_check_dht = tiempo_actual

    # D. LÓGICA DEL CARRUSEL E INTELIGENCIA DE ESTADOS
    if (tiempo_actual - ultimo_cambio) > duracion_actual:
        estado_actual += 1
        
        # Configurar tiempos por defecto
        if estado_actual == 0: duracion_actual = 10 # Madrid
        elif estado_actual == 1: duracion_actual = 6  # Clima Int
        elif estado_actual == 2: duracion_actual = 6  # Espectro
        elif estado_actual == 3: duracion_actual = 10 # Panama
        elif estado_actual == 4: duracion_actual = 6  # Clima Ext
        
        elif estado_actual == 5: # Efemérides
            efemeride_hoy = obtener_efemeride()
            if not efemeride_hoy:
                estado_actual = 6 # ¡Saltar directamente al dato curioso!
            else:
                # Si hay efeméride, le damos 6 segundos para leerla
                duracion_actual = 6 

        if estado_actual == 6: # Dato Curioso (Paginación Dinámica)
            # Calculamos cuántas páginas de 3 líneas necesitamos
            paginas = (len(api_fact_lineas) // 3) + 1
            duracion_actual = paginas * 4 # 4 segundos por página
            
        if estado_actual > 6:
            estado_actual = 0
            duracion_actual = 10
            
        ultimo_cambio = tiempo_actual

    # E. DIBUJAR PANTALLA
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
    draw.line((0, 16, 128, 16), fill=255)

    if estado_actual == 0:
        draw.text((20 + offset_x, 0 + offset_y), "MADRID", font=font_titulo, fill=255)
        draw.text((2 + offset_x, 18 + offset_y), datetime.now(ZoneInfo("Europe/Madrid")).strftime("%H:%M"), font=font_hora, fill=255)

    elif estado_actual == 1:
        draw.text((15 + offset_x, 0 + offset_y), "CLIMA INTERIOR", font=font_titulo, fill=255)
        draw.text((5 + offset_x, 18 + offset_y), "\uf2c9", font=font_iconos, fill=255)
        draw.text((30 + offset_x, 18 + offset_y), ultima_temp_int, font=font_datos, fill=255)
        draw.text((5 + offset_x, 42 + offset_y), "\uf043", font=font_iconos, fill=255)
        draw.text((30 + offset_x, 46 + offset_y), ultima_hum_int, font=font_titulo, fill=255)

    elif estado_actual == 2:
        draw.text((10 + offset_x, 0 + offset_y), "ESPECTRO LUZ", font=font_titulo, fill=255)
        if sensor_luz:
            try:
                canales = [sensor_luz.channel_415nm, sensor_luz.channel_445nm, sensor_luz.channel_480nm, sensor_luz.channel_515nm, sensor_luz.channel_555nm, sensor_luz.channel_590nm, sensor_luz.channel_630nm, sensor_luz.channel_680nm]
                max_val = max(canales) if max(canales) > 0 else 1
                for i, v in enumerate(canales):
                    draw.rectangle((2 + (i * 16), 64 - int((v / max_val) * 45), 14 + (i * 16), 64), fill=255)
            except: pass

    elif estado_actual == 3:
        draw.text((18 + offset_x, 0 + offset_y), "PANAMA", font=font_titulo, fill=255)
        draw.text((2 + offset_x, 18 + offset_y), datetime.now(ZoneInfo("America/Panama")).strftime("%H:%M"), font=font_hora, fill=255)

    elif estado_actual == 4:
        draw.text((15 + offset_x, 0 + offset_y), "CLIMA MADRID", font=font_titulo, fill=255)
        draw.text((5 + offset_x, 18 + offset_y), "\uf0c2", font=font_iconos, fill=255)
        draw.text((35 + offset_x, 18 + offset_y), api_temp_ext, font=font_datos, fill=255)
        draw.text((5 + offset_x, 48 + offset_y), api_pronostico, font=font_titulo, fill=255)

    elif estado_actual == 5:
        draw.text((20 + offset_x, 0 + offset_y), "UN DIA COMO HOY", font=font_titulo, fill=255)
        lineas_efemeride = obtener_efemeride()
        if lineas_efemeride:
            y_text = 20
            # Las efemérides suelen ser cortas, mostramos las primeras 3 líneas
            for linea in lineas_efemeride[:3]: 
                draw.text((5 + offset_x, y_text + offset_y), linea, font=font_texto, fill=255)
                y_text += 14

    elif estado_actual == 6:
        draw.text((20 + offset_x, 0 + offset_y), "Fun fact!", font=font_titulo, fill=255)
        
        # --- LÓGICA DE PAGINACIÓN ---
        segundos_transcurridos = tiempo_actual - ultimo_cambio
        pagina_actual = int(segundos_transcurridos // 4) # Cambia de página cada 4s
        
        inicio = pagina_actual * 3
        fin = inicio + 3
        
        y_text = 20
        # Mostramos solo las 3 líneas de la página actual
        for linea in api_fact_lineas[inicio:fin]:
            draw.text((5 + offset_x, y_text + offset_y), linea, font=font_texto, fill=255)
            y_text += 14

    oled.image(image)
    oled.show()
    time.sleep(0.1)
