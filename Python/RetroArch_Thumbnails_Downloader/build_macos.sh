#!/bin/bash

echo "Construyendo RetroArch Thumbnails Downloader para macOS..."

# Check if virtual environment exists
# Comprobar si existe un entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando un entorno virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
# Activar entorno virtual
source venv/bin/activate

# Install dependencies
# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller
# Construir con PyInstaller
echo "Paquete de aplicaciones de construcción..."
python -m PyInstaller retro_thumbnails.spec --clean --noconfirm

# Create dist directory if it doesn't exist
# Crear directorio dist si no existe
mkdir -p dist/macos

# Copy app bundle to dist directory
# Copiar el paquete de aplicaciones al directorio dist
if [ -d "dist/RetroArch Thumbnails Downloader.app" ]; then
    cp -r "dist/RetroArch Thumbnails Downloader.app" "dist/macos/"
    echo "¡Construcción completada con éxito!"
    echo "Paquete de aplicaciones ubicado en: dist/macos/RetroArch Thumbnails Downloader.app"
else
    echo "¡Error de construcción!"
fi

# Deactivate virtual environment
# Desactivar entorno virtual
deactivate
