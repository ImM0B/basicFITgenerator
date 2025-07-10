# 🏋️‍♂️ Basic-FIT QR Generator

Generador automático de códigos QR para Basic-FIT con soporte para ejecución continua o única.

## 📋 Requisitos

- Python 3.x
- Conexión a Internet
- Las siguientes bibliotecas de Python:
  - requests
  - colorama
  - beautifulsoup4
  - pillow
  - qrcode

## 🚀 Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tu-usuario/basicFITgenerator.git
cd basicFITgenerator
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 💻 Uso

El script puede ejecutarse de dos formas:

### Modo una sola ejecución
```bash
python basicFITgenerator.py
```
Esto generará un solo código QR y terminará.

### Modo continuo
```bash
python basicFITgenerator.py -t 8
```
Esto generará códigos QR cada 8 horas.

### Opciones disponibles

- `-t, --time`: Tiempo en horas entre cada generación (por defecto: 8)
- `-n, --name`: Nombre para la cuenta (por defecto: Joan)
- `-l, --lastname`: Apellido para la cuenta (por defecto: Pradells)
- `-d, --date`: Fecha de nacimiento en formato YYYY-MM-DD (por defecto: 1996-12-23)

### Ejemplos

```bash
# Usar valores por defecto
python basicFITgenerator.py

# Ejecutar cada 12 horas
python basicFITgenerator.py -t 12

# Personalizar datos
python basicFITgenerator.py -n "Juan" -l "García" -d "1995-05-15"
```

## 📝 Notas

- El código QR se guarda como `last_qr.png` en el directorio actual
- El script utiliza correos temporales para el registro
- Se puede interrumpir el proceso en cualquier momento con Ctrl+C

## ⚠️ Advertencia

Este script es solo para fines educativos. Úsalo de manera responsable y respetando los términos de servicio de Basic-FIT.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 