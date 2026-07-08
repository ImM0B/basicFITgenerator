# Basic-FIT Generator

Generador automático de cuentas y códigos QR para Basic-Fit con dos modos de funcionamiento:

- Modo app: crea un correo temporal, registra la cuenta y completa el proceso de establecimiento de contraseña.
- Modo qr: crea un correo temporal y recupera el código QR desde el correo recibido.

## Requisitos

- Python 3.x
- Conexión a Internet
- Dependencias de Python:
  - requests
  - colorama
  - beautifulsoup4
  - pillow
  - qrcode
  - rich

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/ImM0B/basicFITgenerator.git
cd basicFITgenerator
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Modo app
```bash
python basicFITgenerator.py app
```
Este modo crea un correo temporal, registra la cuenta en Basic-Fit, espera al correo de restablecimiento de contraseña y finaliza mostrando las credenciales generadas.

### Modo qr
```bash
python basicFITgenerator.py qr
```
Este modo crea un correo temporal, registra la cuenta y recupera el código QR desde el correo recibido.

### Ejecución repetida en modo qr
```bash
python basicFITgenerator.py qr -t 12
```
Esto repite el proceso cada 12 horas.

## Opciones disponibles

- `mode`: obligatorio. Valores: `app` o `qr`
- `-t, --time`: tiempo en horas entre ejecuciones (por defecto: 8)
- `-n, --name`: nombre para la cuenta (por defecto: Joan)
- `-l, --lastname`: apellido para la cuenta (por defecto: Pradells)
- `-d, --date`: fecha de nacimiento en formato YYYY-MM-DD (por defecto: 1996-12-23)
- `-e, --email`: correo personalizado (opcional, actualmente no se usa en el flujo de app)
- `-c, --campaign-id`: campaign ID personalizado (por defecto: vacío)
- `-v, --verbose`: muestra información detallada de las peticiones y respuestas

## Ejemplos

```bash
# Modo app completo
python basicFITgenerator.py app

# Modo qr cada 12 horas
python basicFITgenerator.py qr -t 12

# Modo qr con datos personalizados
python basicFITgenerator.py qr -n "Juan" -l "García" -d "1995-05-15"

# Modo app con campaign ID personalizado
python basicFITgenerator.py app -c "mi-campaign-id"
```

## Notas

- La salida está formateada con Rich y paneles para una experiencia más limpia en consola.
- El código QR se guarda en un directorio `basicQRs` junto al proyecto.
- Se puede interrumpir el proceso en cualquier momento con Ctrl+C.

## Advertencia

Este script es solo para fines educativos. Úsalo de manera responsable y respetando los términos de servicio de Basic-Fit.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.
