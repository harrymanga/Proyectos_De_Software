#!/usr/bin/env bash
# Compila e instala appimage-builder en macOS (venv + wheel + smoke tests).
#
# Nota: los AppImage son solo para Linux; en macOS se instala el paquete
# (CLI + GUI Qt) para desarrollo y uso local.
#
# Uso:
#   scripts/build-macos.sh
#
# Variables de entorno:
#   VENV_DIR   Directorio del venv (defecto: <repo>/.venv)
#   WITH_DEV=0 Omite extras dev/gui/build (solo instala el paquete)
#   BUILD_DIST=1 Genera sdist/wheel en dist/ (defecto: 1)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
WITH_DEV="${WITH_DEV:-1}"
BUILD_DIST="${BUILD_DIST:-1}"

log() { printf '[build-macos] %s\n' "$*"; }
die() { printf '[build-macos] ERROR: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 no encontrado (instala Python 3.11+ o Xcode tools)"
PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
log "Python detectado: $PYVER"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
    || die "se requiere Python >= 3.11 (tienes $PYVER)"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    log "Creando venv en $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip

if [ "$WITH_DEV" = "1" ]; then
    log "Instalando paquete + extras (dev,gui,build)"
    "$VENV_DIR/bin/pip" install -e "${ROOT}[dev,gui,build]"
else
    log "Instalando solo el paquete"
    "$VENV_DIR/bin/pip" install "$ROOT"
fi

if [ "$BUILD_DIST" = "1" ]; then
    log "Generando sdist/wheel"
    "$VENV_DIR/bin/pip" install --quiet build
    rm -rf "$ROOT/dist" && mkdir -p "$ROOT/dist"
    "$VENV_DIR/bin/python" -m build "$ROOT" --outdir "$ROOT/dist"
fi

log "Smoke tests"
"$VENV_DIR/bin/appimage-builder" --version
"$VENV_DIR/bin/appimage-builder" template list > /dev/null
QT_QPA_PLATFORM=offscreen "$VENV_DIR/bin/python" -c \
    "from appimage_builder.gui.wizard.wizard import AppImageWizard; print('GUI OK')"

log "OK: venv=$VENV_DIR"
log "Nota: 'appimage-builder build/doctor' está orientado a Linux (AppImage)."
