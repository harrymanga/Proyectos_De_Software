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

# Install desktop entry + icon (el binario ELF no lleva icono propio en Linux)
# Instalar lanzador e icono para que el icono aparezca en menú/dock
if [ -f "retro-thumbnails.desktop" ] && [ -f "icons/retro-thumbnails.png" ]; then
    APPS_DIR="$HOME/.local/share/applications"
    ICONS_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
    mkdir -p "$APPS_DIR" "$ICONS_DIR"
    sed "s|^Exec=.*|Exec=\"${PWD}/dist/linux/RetroArch Thumbnails Downloader\"|" \
        retro-thumbnails.desktop > "$APPS_DIR/retro-thumbnails.desktop"
    cp "icons/retro-thumbnails.png" "$ICONS_DIR/retro-thumbnails.png"
    command -v desktop-file-validate >/dev/null \
        && desktop-file-validate "$APPS_DIR/retro-thumbnails.desktop" \
        && echo "Lanzador instalado en: $APPS_DIR/retro-thumbnails.desktop"
    command -v update-desktop-database >/dev/null \
        && update-desktop-database "$APPS_DIR" 2>/dev/null
fi

# Deactivate virtual environment
# Desactivar entorno virtual
deactivate
