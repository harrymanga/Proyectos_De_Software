#!/usr/bin/env bash
# Compila e instala appimage-builder en Linux (venv + wheel + smoke tests).
#
# Uso:
#   scripts/build-linux.sh [opciones]
#
# Variables de entorno:
#   VENV_DIR     Directorio del venv (defecto: <repo>/.venv)
#   WITH_DEV=0   Omite extras dev/gui/build (solo instala el paquete)
#   BUILD_DIST=1 Genera sdist/wheel en dist/ (defecto: 1)
#   INSTALL_DESKTOP=1 Instala el .desktop de la GUI en ~/.local/share/applications
#   APPIMAGE=1   Además genera el AppImage con scripts/build-appimage.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
WITH_DEV="${WITH_DEV:-1}"
BUILD_DIST="${BUILD_DIST:-1}"
INSTALL_DESKTOP="${INSTALL_DESKTOP:-0}"
APPIMAGE="${APPIMAGE:-0}"

log() { printf '[build-linux] %s\n' "$*"; }
die() { printf '[build-linux] ERROR: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 no encontrado"
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
"$VENV_DIR/bin/appimage-builder" doctor --json > /dev/null
"$VENV_DIR/bin/appimage-builder" template list > /dev/null

if [ "$INSTALL_DESKTOP" = "1" ]; then
    log "Instalando entrada de escritorio"
    APPS_DIR="$HOME/.local/share/applications"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$APPS_DIR" "$BIN_DIR"
    printf '#!/bin/sh\nexec "%s/bin/appimage-builder" "$@"\n' "$VENV_DIR" > "$BIN_DIR/appimage-builder"
    printf '#!/bin/sh\nexec "%s/bin/appimage-builder-gui" "$@"\n' "$VENV_DIR" > "$BIN_DIR/appimage-builder-gui"
    chmod +x "$BIN_DIR/appimage-builder" "$BIN_DIR/appimage-builder-gui"
    if [ -f "$ROOT/assets/icon-512.png" ]; then
        log "Instalando iconos propios"
        for size in 32 64 128 256 512; do
            dest="$HOME/.local/share/icons/hicolor/${size}x${size}/apps"
            mkdir -p "$dest"
            cp "$ROOT/assets/icon-${size}.png" "$dest/appimage-builder.png"
        done
        ICON_NAME="appimage-builder"
    else
        log "Sin assets/icon-*.png: icono genérico"
        ICON_NAME="package-x-generic"
    fi
    cat > "$APPS_DIR/appimage-builder.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=appimage-builder
GenericName=Creador de AppImages
Comment=Crea AppImages de forma automatizada (CLI y GUI intuitiva)
Exec=$BIN_DIR/appimage-builder-gui %F
Icon=$ICON_NAME
Terminal=false
Categories=Development;
StartupNotify=true
StartupWMClass=appimagebuilder
Keywords=appimage;packaging;linux;
EOF
    command -v desktop-file-validate >/dev/null \
        && desktop-file-validate "$APPS_DIR/appimage-builder.desktop" \
        && log ".desktop válido"
fi

if [ "$APPIMAGE" = "1" ]; then
    log "Generando AppImage (receta dogfood)"
    APPIMAGE_OUTPUT="${APPIMAGE_OUTPUT:-$ROOT/dist}" \
        "$ROOT/scripts/build-appimage.sh"
fi

log "OK: venv=$VENV_DIR"
