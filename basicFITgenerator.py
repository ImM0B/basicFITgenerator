#!/usr/bin/env python3
import requests, sys, signal, time, colorama, json, re, os, string, random, argparse, warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from colorama import Fore, Style, init
from urllib.parse import urlparse, parse_qs
from rich.console import Console
from rich.panel import Panel
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import itertools
import threading
import qrcode
from PIL import Image
from io import BytesIO
import base64
warnings.simplefilter('ignore', InsecureRequestWarning)
init()
console = Console(width=120, force_terminal=True, color_system="auto")


def emit_panel(message, title="Info", style="cyan"):
    console.print(Panel(message, title=title, border_style=style, expand=True, padding=(0, 2)))

def sig_handler(sig, frame):
    emit_panel("Saliendo...", "Salida", "red")
    sys.exit(0)
signal.signal(signal.SIGINT, sig_handler)

class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        if action.option_strings:
            action.help = Fore.CYAN + action.help + Style.RESET_ALL
        return super()._format_action(action)
    def _format_usage(self, usage, actions, groups, prefix):
        return Fore.YELLOW + super()._format_usage(usage, actions, groups, prefix) + Style.RESET_ALL
    def _format_text(self, text):
        if text:
            return Fore.GREEN + text + Style.RESET_ALL
        return text

parser = argparse.ArgumentParser(
    description=Fore.GREEN + 'Generador automático de cuentas y códigos QR para Basic-Fit' + Style.RESET_ALL,
    formatter_class=ColoredHelpFormatter,
    epilog=Fore.YELLOW + '''
Modos disponibles:
  app: crea un correo temporal y confirma la cuenta, mostrando las credenciales para loguearse desde la app
  qr : crea un correo temporal y obtiene el código QR desde el correo recibido

Ejemplos de uso:
  python basicFITgenerator.py app                                      # Modo app con flujo completo
  python basicFITgenerator.py qr -t 12                                  # Modo QR cada 12 horas
  python basicFITgenerator.py qr -n "Juan" -l "García" -d "1995-05-15"  # Modo QR con datos personalizados
  python basicFITgenerator.py app -c "mi-campaign-id"                  # Modo app con campaign ID personalizado
''' + Style.RESET_ALL)

parser.add_argument('mode', choices=['app', 'qr'], help='Modo de operación: app o qr')
parser.add_argument('-t', '--time',        type=int, help='Tiempo en horas entre cada ejecución (por defecto: 8)')
parser.add_argument('-n', '--name',        type=str, help='Nombre para la cuenta (por defecto: Joan)')
parser.add_argument('-l', '--lastname',    type=str, help='Apellido para la cuenta (por defecto: Pradells)')
parser.add_argument('-d', '--date',        type=str, help='Fecha de nacimiento en formato YYYY-MM-DD (por defecto: 1996-12-23)')
parser.add_argument('-e', '--email',       type=str, help='Correo personalizado (en lugar de generar uno temporal)')
parser.add_argument('-c', '--campaign-id', type=str, help='Campaign ID personalizado (por defecto: vacío)')
parser.add_argument('-v', '--verbose',     action='store_true', help='Muestra información detallada de las peticiones y respuestas')
args = parser.parse_args()

# Valores por defecto
modo              = args.mode
intervalo_horas   = args.time          if args.time     else 8
nombre            = args.name          if args.name     else "Joan"
apellido          = args.lastname      if args.lastname else "Pradells"
fecha_nacimiento  = args.date          if args.date     else "1996-12-23"
campaign_id       = args.campaign_id   if args.campaign_id else ""
verbose           = args.verbose

# Variables globales
mail_url   = "https://api.mail.tm"
basic_url  = "https://member.basic-fit.com/api/signUpForm/signUp"
password   = "basicbasicFIT1234"
header     = {"Content-Type": "application/json"}
headers    = {
    "Cookie": "bf-locale=es-ES; bf-country=ES",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json"
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
    session = requests.Session()

    # ── CREAR CORREO DESECHABLE Y TOKEN ─────────────────────────────────────
    result = session.get(f"{mail_url}/domains", verify=False)
    vprint(f"[DEBUG] Respuesta dominios: {result.text}")
    result_dict  = json.loads(result.text)
    mail_domain  = result_dict['hydra:member'][0]['domain']
    userID       = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    email        = f"{userID}@{mail_domain}"
    payload      = {"address": f"{email}", "password": f"{password}"}

    result = session.post(f"{mail_url}/accounts", json=payload, headers=header, timeout=5, verify=False)
    vprint(f"[DEBUG] Respuesta creación cuenta mail: {result.text}")
    if result.status_code == 201:
        emit_panel("[bold yellow]Mail desechable creado[/]", "Paso 1", "yellow")
    else:
        emit_panel("[bold red]Fallo al crear el mail[/]", "Error", "red")
        return False

    # ── EXTRAER TOKEN DEL SERVICIO DE MAIL ──────────────────────────────────
    result      = session.post(f"{mail_url}/token", json=payload, headers=header, timeout=5, verify=False)
    vprint(f"[DEBUG] Respuesta token: {result.text}")
    result_dict = json.loads(result.text)
    token       = result_dict['token']
    if result.status_code == 200:
        emit_panel("[bold yellow]Token extraído correctamente[/]", "Paso 2", "yellow")
    else:
        emit_panel("[bold red]Fallo al extraer el token[/]", "Error", "red")
        return False

    # ── CREAR CUENTA BASICFIT ─────────────────────────────────────────────────
    body = {
        "firstName":       nombre,
        "lastName":        apellido,
        "email":           f"{email}",
        "locale":          "es-ES",
        "dateOfBirth":     f"{fecha_nacimiento}",
        "tos":             True,
        "campaignId":      campaign_id,
        "ageConfirmation": True,
        "conditionalFields":{}
    }

    result = session.post(basic_url, json=body, headers=headers, timeout=5, verify=False)
    vprint(f"[DEBUG] Respuesta creación Basic-Fit: {result.text}")
    if result.status_code == 200:
        emit_panel("[bold green]Cuenta Basic-Fit creada[/]", "Paso 3", "green")
    else:
        emit_panel("[bold red]Fallo al crear la cuenta Basic-Fit[/]", "Error", "red")
        return False

    # ── OBTENER QR O FINALIZAR EL PROCESO ────────────────────────────────────
    if modo == 'app':
        emit_panel(f"[bold cyan]Registro completado con el correo:[/]\n{email}", "Modo app", "cyan")
        emit_panel("[bold yellow]Revisa tu bandeja de entrada (y spam) para obtener el correo de confirmación.[/]", "Paso 4", "yellow")
        emit_panel(f"[bold green]Para terminar el proceso introduce el correo '{email}' en la opción 'Establece tu contraseña' desde https://login.basic-fit.com/[/]", "Siguiente paso", "green")

        emit_panel("[bold yellow]Esperando el correo de restablecimiento de contraseña...[/]", "Espera", "yellow")
        reset_url = None
        for _ in range(24):
            result = session.get(
                f"{mail_url}/messages",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                timeout=5, verify=False
            )
            vprint(f"[DEBUG] Respuesta mensajes app: {result.text}")
            if result.status_code == 200:
                result_dict = json.loads(result.text)
                for message in result_dict.get('hydra:member', []):
                    download_url = message.get('downloadUrl')
                    if not download_url:
                        continue
                    msg_result = session.get(
                        f"{mail_url}{download_url}",
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                        timeout=5, verify=False
                    )
                    if msg_result.status_code == 200:
                        body_text = msg_result.text
                        matches = re.findall(r'https://login\.basic-fit\.com/set-password[^\s"\'<>]*', body_text)
                        if matches:
                            reset_url = matches[0]
                            break
                if reset_url:
                    break
            time.sleep(5)

        if not reset_url:
            emit_panel("No se encontró el enlace de restablecimiento de contraseña en el correo", "Error", "red")
            return False

        parsed_url = urlparse(reset_url)
        reset_token = parse_qs(parsed_url.query).get('token', [None])[0]
        if not reset_token:
            emit_panel("No se pudo extraer el token del enlace de restablecimiento", "Error", "red")
            return False

        set_password_url = "https://login.basic-fit.com/set-password"
        set_password_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Reset-Token": reset_token,
            "User-Agent": headers["User-Agent"],
            "Origin": "https://login.basic-fit.com",
            "Client-Id": "5T2sVjv1ViH1FExCeRsXuT4EeLw91au1D2kpQS_4T3o",
            "Redirect-Uri": "https://my.basic-fit.com/sso",
            "Referer": reset_url
        }
        random_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        set_password_payload = {"password": random_password, "passwordConfirm": random_password}

        vprint(f"[DEBUG] Petición set-password URL: {set_password_url}")
        vprint(f"[DEBUG] Petición set-password Headers: {json.dumps(set_password_headers, indent=2)}")
        vprint(f"[DEBUG] Petición set-password Payload: {json.dumps(set_password_payload, indent=2)}")

        set_password_result = session.post(
            set_password_url,
            json=set_password_payload,
            headers=set_password_headers,
            timeout=10,
            verify=False
        )
        vprint(f"[DEBUG] Respuesta set-password: {set_password_result.text}")
        if set_password_result.status_code == 200:
            try:
                response_json = set_password_result.json()
                if response_json.get('message') == 'OK':
                    emit_panel("[bold green]Contraseña establecida correctamente[/]", "Éxito", "green")
                    emit_panel(f"[bold cyan]Correo:[/] {email}\n[bold cyan]Contraseña:[/] {random_password}", "Credenciales", "cyan")
                    return True
            except ValueError:
                pass
        emit_panel(f"Error al establecer la contraseña: {set_password_result.text}", "Error", "red")
        return False

    # Modo QR: esperar y extraer QR del mail desechable
    emit_panel("Esperando a recibir el correo con el QR...", "Espera", "yellow")
    time.sleep(30)

    result = session.get(
        f"{mail_url}/messages",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        timeout=5, verify=False
    )
    vprint(f"[DEBUG] Respuesta mensajes: {result.text}")
    result_dict = json.loads(result.text)
    url_source  = result_dict['hydra:member'][0]['downloadUrl']

    result = session.get(
        f"{mail_url}{url_source}",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        timeout=5, verify=False
    )
    vprint(f"[DEBUG] Respuesta mensaje QR: {result.text}")
    qr_url = re.findall(r'https?://[^\s"\'<>]*qr-code-generator[^\s"\'<>]*', result.text)

    if not qr_url:
        emit_panel("No se encontró el enlace del QR en el correo", "Error", "red")
        return False

    emit_panel("QR conseguido", "Éxito", "green")
    emit_panel(f"Enlace al QR:\n{qr_url[0]}", "QR", "cyan")

    # Descargar y guardar el QR
    qr_response = requests.get(qr_url[0])
    vprint(f"[DEBUG] Respuesta descarga QR: {qr_response.status_code}")

    if qr_response.status_code == 200:
        match = re.search(r"D(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", qr_url[0])
        if match:
            year       = '20' + match.group(1)
            month      = match.group(2)
            day        = match.group(3)
            hour       = match.group(4)
            minute     = match.group(5)
            fecha_str  = f"{year}{month}{day}_{hour}{minute}"
            nombre_archivo = f"{fecha_str}.png"
        else:
            nombre_archivo = 'qr_sin_fecha.png'

        carpeta_qr = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'basicQRs'))
        if not os.path.exists(carpeta_qr):
            os.makedirs(carpeta_qr)

        ruta_archivo = os.path.join(carpeta_qr, nombre_archivo)
        qr_image     = Image.open(BytesIO(qr_response.content))
        qr_image.save(ruta_archivo)
        emit_panel(f"Código QR guardado como:\n{ruta_archivo}", "Archivo", "yellow")
    else:
        emit_panel("Error al descargar el QR", "Error", "red")
        return False

    return True

# ── BUCLE PRINCIPAL ───────────────────────────────────────────────────────────
while True:
    emit_panel(f"[bold cyan]Iniciando generación de cuenta - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]", "Inicio", "cyan")
    exito = generar_cuenta()

    if exito:
        emit_panel("Proceso completado", "Éxito", "green")
    else:
        emit_panel("Error en el proceso. Activa el modo verbose para ver el detalle de error o usa otro CampaignId", "Error", "red")

    # Modo app: ejecutar una sola vez
    if modo == 'app':
        sys.exit(0)

    # Modo qr: ejecutar con intervalo
    if args.time:
        emit_panel(f"Próxima ejecución en {intervalo_horas} horas", "Espera", "cyan")
        animacion_thread        = threading.Thread(target=animacion_espera)
        animacion_thread.daemon = True
        animacion_thread.start()
        time.sleep(intervalo_horas * 3600)
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    else:
        emit_panel("Finalizando programa...", "Fin", "green")
        sys.exit(0)
