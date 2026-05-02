#!/bin/bash

echo "Construyendo RetroArch Thumbnails Downloader para Linux..."

# Check if virtual environment exists
# Comprobar si existe un entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando un entorno virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
# Activar el entorno virtual
source venv/bin/activate

# Install dependencies
# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller
# Construir con PyInstaller
echo "Construyendo ejecutable..."
python -m PyInstaller retro_thumbnails.spec --clean --noconfirm

# Create dist directory if it doesn't exist
# Crear directorio dist si no existe
mkdir -p dist/linux

# Copy executable to dist directory
# Copiar ejecutable al directorio dist
if [ -f "dist/RetroArch Thumbnails Downloader" ]; then
    cp "dist/RetroArch Thumbnails Downloader" "dist/linux/"
    chmod +x "dist/linux/RetroArch Thumbnails Downloader"
    echo "¡Construcción completada con éxito!"
    echo "Ejecutable ubicado en: dist/linux/RetroArch Thumbnails Downloader"
else
    echo "¡Error de construcción!"
fi

# Deactivate virtual environment
# Desactivar entorno virtual
deactivate
