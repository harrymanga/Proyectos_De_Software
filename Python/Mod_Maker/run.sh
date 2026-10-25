#!/usr/bin/env bash
# Lanzador para Linux y macOS
# Crea el entorno virtual, instala dependencias y ejecuta la aplicación.
# Norma §56: arranque sin fricción.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYTHON_CMD="python3"

# Detectar sistema operativo
OS="$(uname -s)"

echo "[Mod_Maker] Iniciando lanzador en $OS..."

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "[Mod_Maker] Creando entorno virtual en $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activar entorno virtual
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Instalar dependencias
if [ -f requirements.txt ]; then
    echo "[Mod_Maker] Instalando dependencias desde requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Resolver paquetes del sistema si existen
if [ -f system-packages.txt ]; then
    echo "[Mod_Maker] Revisando paquetes del sistema declarados en system-packages.txt..."
    while IFS= read -r pkg || [ -n "$pkg" ]; do
        # Ignorar comentarios y líneas vacías
        case "$pkg" in
            \#*|"") continue ;;
        esac
        echo "[Mod_Maker] Paquete del sistema declarado: $pkg (instalación manual si es necesario)"
    done < system-packages.txt
fi

# Ejecutar la aplicación
echo "[Mod_Maker] Ejecutando Mod_Maker..."
python -m src.gui.main_window
