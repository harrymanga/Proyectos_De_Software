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
    echo "[Mod_Maker] Revisando dependencias desde requirements.txt..."
    # Verificar si faltan dependencias sin mostrar salida completa
    if pip install --upgrade pip --quiet 2>/dev/null; then
        if pip install -r requirements.txt --quiet 2>/tmp/pip_install_err.log; then
            echo "[Mod_Maker] Dependencias instaladas correctamente"
        else
            echo "[Mod_Maker] Instalando dependencias faltantes..."
            pip install --upgrade pip
            pip install -r requirements.txt
        fi
    else
        echo "[Mod_Maker] Error actualizando pip. Intentando continuar..."
    fi
fi

# Resolver paquetes del sistema si existen
if [ -f system-packages.txt ]; then
    echo "[Mod_Maker] Revisando paquetes del sistema declarados en system-packages.txt..."
    while IFS= read -r pkg || [ -n "$pkg" ]; do
        # Ignorar comentarios y líneas vacías
        case "$pkg" in
            \#*|"") continue ;;
        esac
        echo "[Mod_Maker] Paquete del sistema declarado: $pkg (instalación manual si es necesaria)"
    done < system-packages.txt
fi

# Determinar modo de ejecución
MODO="gui"
if [ $# -gt 0 ]; then
    caso_primero="$1"
    case "$caso_primero" in
        gui|gui*)
            MODO="gui"
            ;;
        cli|cli*)
            MODO="cli"
            shift
            ;;
        *)
            # Si el primer argumento no es "gui" ni "cli", asume CLI
            MODO="cli"
            ;;
    esac
fi

# Ejecutar la aplicación
if [ "$MODO" = "cli" ]; then
    echo "[Mod_Maker] Ejecutando Mod_Maker CLI..."
    python -m src.cli.mod_cli "$@"
else
    echo "[Mod_Maker] Ejecutando Mod_Maker GUI..."
    python -m src.gui.main_window
fi