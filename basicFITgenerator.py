#!/usr/bin/env python3

import requests, sys, signal, time, colorama, json, re, os, string, random, argparse
from colorama import Fore, Style, init
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import itertools
import threading
import qrcode
from PIL import Image
from io import BytesIO
import base64
init()

def sig_handler(sig, frame):
    print(Fore.RED + "\n\n[!] Saliendo...\n")
    sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)

# Configuración de argumentos
class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        # Colorear el nombre del argumento
        if action.option_strings:
            action.help = Fore.CYAN + action.help + Style.RESET_ALL
        return super()._format_action(action)

    def _format_usage(self, usage, actions, groups, prefix):
        # Colorear el texto de uso
        return Fore.YELLOW + super()._format_usage(usage, actions, groups, prefix) + Style.RESET_ALL

    def _format_text(self, text):
        # Colorear la descripción y epílogo
        if text:
            return Fore.GREEN + text + Style.RESET_ALL
        return text

parser = argparse.ArgumentParser(
    description=Fore.GREEN + 'Generador automático de códigos QR para Basic-Fit' + Style.RESET_ALL,
    formatter_class=ColoredHelpFormatter,
    epilog=Fore.YELLOW + '''
Ejemplos de uso:
  python basicFITgenerator.py              # Usa valores por defecto
  python basicFITgenerator.py -t 12        # Ejecuta cada 12 horas
  python basicFITgenerator.py -n "Juan" -l "García" -d "1995-05-15"  # Personaliza datos
''' + Style.RESET_ALL)

parser.add_argument('-t', '--time', type=int, help='Tiempo en horas entre cada generación (por defecto: 8)')
parser.add_argument('-n', '--name', type=str, help='Nombre para la cuenta (por defecto: Joan)')
parser.add_argument('-l', '--lastname', type=str, help='Apellido para la cuenta (por defecto: Pradells)')
parser.add_argument('-d', '--date', type=str, help='Fecha de nacimiento en formato YYYY-MM-DD (por defecto: 1996-12-23)')
parser.add_argument('-v', '--verbose', action='store_true', help='Muestra información detallada del proceso')

args = parser.parse_args()

# Valores por defecto
intervalo_horas = args.time if args.time else 8
nombre = args.name if args.name else "Joan"
apellido = args.lastname if args.lastname else "Pradells"
fecha_nacimiento = args.date if args.date else "1996-12-23"
verbose = args.verbose

# Variables
mail_url= "https://api.mail.tm"
basic_url= "https://member.basic-fit.com/api/signUpForm/signUp"
password = "basicbasicFIT1234" #Contraseña por defecto para el correo desechable
header={"Content-Type":"application/json"}
headers = {
    "Cookie": "bf-locale=es-ES; bf-country=ES",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json",
    "Newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjM1MDcxMjkiLCJhcCI6IjUzODU2OTgxMyIsImlkIjoiODM5ZDg4ZjgzODUwNjgwZSIsInRyIjoiZWJkMThhYTk4ZjhhYjc3OTRjNjMxMjZiYjAxMjFjODQiLCJ0aSI6MTc1MTczNzU3NjY1MX19"
}

def vprint(*a, **k):
    if verbose:
        print(*a, **k)

def animacion_espera():
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    while True:
        sys.stdout.write('\r' + Fore.CYAN + f'[{next(spinner)}] Esperando próxima ejecución...')
        sys.stdout.flush()
        time.sleep(0.1)

def generar_cuenta():
    #MAIN
    session = requests.Session()

    #CREAR CORREO
    result = session.get(f"{mail_url}/domains") #Sacamos dominio de correo
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta dominios: {result.text}")
    result_dict= json.loads(result.text)
    mail_domain = result_dict['hydra:member'][0]['domain']
    userID = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12)) #Generamos ID de usuario aleatorio
    email = f"{userID}@{mail_domain}" #Generamos correo aleatorio
    payload= {"address" : f"{email}" , "password" : f"{password}"}
    result = session.post(f"{mail_url}/accounts", json=payload, headers=header ,timeout=5)
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta creación cuenta mail: {result.text}")
    if result.status_code == 201:
        print(Fore.YELLOW + "[1] Mail Desechable Creado")
    else:
        print(Fore.RED + "\n[❗] Fallo al crear el Mail")
        return False

    #EXTRAER TOKEN
    result = session.post(f"{mail_url}/token",json=payload,headers=header,timeout=5)
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta token: {result.text}")
    result_dict= json.loads(result.text) #Crea un diccionario con el resultado en formato json
    token= result_dict['token'] #Del diccionario selecciona el token
    if result.status_code == 200:
        print(Fore.YELLOW + "[2] Token Extraído")
    else:
        print(Fore.RED + "\n[❗] Fallo al extraer el Token")
        return False

    #CREAR CUENTA BASICFIT
    body = {
        "firstName": nombre,
        "lastName": apellido,
        "email": f"{email}",
        "locale":"es-ES",
        "dateOfBirth": f"{fecha_nacimiento}T00:00:00.000Z",
        "tos": True,
        "campaignId": "1j4E1vAzx2blwpjL4tPcNp",
        "ageConfirmation": True
    }

    result = session.post(basic_url, json=body, headers=headers, timeout=5)
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta creación Basic-Fit: {result.text}")
    if result.status_code == 200:
        print(Fore.YELLOW + "[3] Cuenta Basic-Fit Creada")
    else:
        print(Fore.RED + "\n[❗] Fallo al crear la cuenta Basic-Fit")
        return False

    #EXTRAER QR DEL CORREO
    print(Fore.YELLOW + "[⏳] Esperando a recibir el correo con el QR...")
    time.sleep(30) 
    result = session.get(f"{mail_url}/messages",headers={"Content-Type":"application/json", "Authorization": f"Bearer {token}"},timeout=5)
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta mensajes: {result.text}")
    result_dict= json.loads(result.text)
    url_source = result_dict['hydra:member'][0]['downloadUrl'] #Accedemos al primer elemento de la lista hydra:member y extraemos downloadURL
    result = session.get(f"{mail_url}{url_source}",headers={"Content-Type":"application/json", "Authorization": f"Bearer {token}"},timeout=5)
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta mensaje QR: {result.text}")
    qr_url = re.findall(r'https?://[^\s"\'<>]*qr-code-generator[^\s"\'<>]*', result.text)
    print(Fore.GREEN + "[🏆] QR conseguido")
    print(Fore.CYAN + "[🔗] Enlace al QR:", qr_url[0])

    # Descargar y mostrar el QR

    # Descargar la imagen del QR
    qr_response = requests.get(qr_url[0])
    vprint(Fore.MAGENTA + f"[DEBUG] Respuesta descarga QR: {qr_response.status_code}")
    if qr_response.status_code == 200:
        # Extraer el parámetro tipo D250706123227173 del enlace
        match = re.search(r"D(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", qr_url[0])
        if match:
            # Parsear la fecha y sumar 14 días
            year = int('20' + match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            # El último grupo (7) puede ser un contador, lo ignoramos para la fecha
            fecha_original = datetime(year, month, day, hour, minute, second)
            fecha_final = fecha_original + timedelta(days=14)
            nombre_archivo = fecha_final.strftime('%Y%m%d%H%M%S') + '.png'
        else:
            nombre_archivo = 'qr_sin_fecha.png'
        # Crear carpeta basicQRs en el directorio anterior si no existe
        carpeta_qr = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'basicQRs'))
        if not os.path.exists(carpeta_qr):
            os.makedirs(carpeta_qr)
        ruta_archivo = os.path.join(carpeta_qr, nombre_archivo)
        # Convertir la respuesta a una imagen
        qr_image = Image.open(BytesIO(qr_response.content))
        # Guardar la imagen en la carpeta basicQRs con el nombre adecuado
        qr_image.save(ruta_archivo)
        print(Fore.YELLOW + f"[📱] Código QR guardado como '{ruta_archivo}'")
    else:
        print(Fore.RED + "[❗] Error al descargar el QR")
        return False
    
    return True

# Bucle principal
while True:
    print(Fore.CYAN + f"\n[🔄] Iniciando generación de cuenta - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exito = generar_cuenta()
    if exito:
        print(Fore.GREEN + f"\n[✅] Proceso completado")
    else:
        print(Fore.RED + "\n[❌] Error en el proceso. Se reintentará en el siguiente intervalo...")
    if args.time:
        print(Fore.GREEN + f"[⏳] Próxima ejecución en {intervalo_horas} horas")
        # Iniciar animación en un hilo separado
        animacion_thread = threading.Thread(target=animacion_espera)
        animacion_thread.daemon = True
        animacion_thread.start()
        # Esperar el intervalo especificado
        time.sleep(intervalo_horas * 3600)
        # Limpiar la línea de la animación
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    else:
        print(Fore.GREEN + "[👋] Finalizando programa...")
        sys.exit(0)