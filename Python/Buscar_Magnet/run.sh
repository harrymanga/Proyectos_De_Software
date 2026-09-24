#!/bin/bash
# run.sh — Punto de entrada único: crea .venv, instala dependencias y ejecuta la GUI.
# Uso: ./run.sh [--system]   (en Windows: run.bat)
#   Sin flags: venv aislado. Si system-packages.txt lista módulos que solo
#   existen en el python del sistema, el venv se recrea SOLO con acceso a
#   paquetes del sistema (equivale a --system, automático).
#   --system: fuerza la recreación con paquetes del sistema.
set -e
cd "$(dirname "$0")"

recreate_system() {
    echo "Recreando .venv con paquetes del sistema..."
    rm -rf .venv
    python3 -m venv --system-site-packages .venv
}

if [ "${1:-}" = "--system" ]; then
    recreate_system
    shift || true
fi

[ -x .venv/bin/python ] || python3 -m venv .venv

needs_system=0
if [ -f system-packages.txt ]; then
    while IFS= read -r mod || [ -n "$mod" ]; do
        mod=$(echo "$mod" | tr -d '[:space:]')
        [ -z "$mod" ] && continue
        case "$mod" in \#*) continue;; esac
        if python3 -c "import $mod" 2>/dev/null && ! .venv/bin/python -c "import $mod" 2>/dev/null; then
            if ! .venv/bin/pip install -q "$mod" 2>/dev/null; then
                needs_system=1
            fi
        fi
    done < system-packages.txt
fi

if [ "$needs_system" -eq 1 ]; then
    echo "Módulos solo disponibles en el sistema: activando acceso (--system automático)."
    recreate_system
fi

.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
exec .venv/bin/python src/gui/magnet_gui.py "$@"
