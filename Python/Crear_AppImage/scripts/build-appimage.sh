#!/usr/bin/env bash
# Genera el AppImage dual (CLI+GUI) del propio proyecto (receta verificada).
#
# Uso:
#   APPIMAGE_OUTPUT=dist/ scripts/build-appimage.sh
#   VENV_DIR=/tmp/aib-venv scripts/build-appimage.sh   # reutiliza un venv existente
#   AIB_BIN=/ruta/appimage-builder scripts/build-appimage.sh  # binario explícito
#
# Autosuficiente: si no se da AIB_BIN, crea/usa un venv dentro del proyecto
# ($ROOT/.venv, misma convención que scripts/build-linux.sh) e instala el
# propio proyecto ahí. No usa binarios instalados fuera del proyecto.
# Usa las herramientas vendorizadas en tools/ (sin descargar nada).
# Requiere: python3 (>=3.11), red (solo deps pip) y FUSE
# (o APPIMAGE_EXTRACT_AND_RUN=1) para ejecutar las herramientas.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
AIB_BIN="${AIB_BIN:-$VENV_DIR/bin/appimage-builder}"
APPIMAGE_OUTPUT="${APPIMAGE_OUTPUT:-$ROOT/dist}"
LINUXDEPLOY="$ROOT/tools/linuxdeploy-x86_64.AppImage"
APPIMAGETOOL="$ROOT/tools/appimagetool-x86_64.AppImage"

log() { printf '[build-appimage] %s\n' "$*"; }
die() { printf '[build-appimage] ERROR: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 no encontrado"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
    || die "se requiere Python >= 3.11"

if [ ! -x "$VENV_DIR/bin/appimage-builder" ] && [ "$AIB_BIN" = "$VENV_DIR/bin/appimage-builder" ]; then
    log "Creando venv del proyecto en $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    log "Instalando el propio proyecto en el venv"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -e "$ROOT"
fi
[ -x "$AIB_BIN" ] || die "binario no ejecutable: $AIB_BIN"

# Librerías de drivers SQL de Qt ausentes en el host (verificado en deploy).
EXCLUDES=(
    libpq.so.5
    libodbc.so.2
    libodbcinst.so.2
    libclntsh.so.23.1
    libmysqlclient.so.21
    libmariadb.so.3
    libmimerapi.so
    libfbclient.so.2
)

EXCLUDE_ARGS=()
for lib in "${EXCLUDES[@]}"; do
    EXCLUDE_ARGS+=(--exclude-library "$lib")
done

mkdir -p "$APPIMAGE_OUTPUT"
for tool in "$LINUXDEPLOY" "$APPIMAGETOOL"; do
    if [ ! -x "$tool" ]; then
        printf '[build-appimage] ERROR: falta herramienta vendorizada: %s\n' "$tool" >&2
        exit 1
    fi
done
ICON_ARGS=()
if [ -f "$ROOT/assets/icon-512.png" ]; then
    ICON_ARGS=(--icon "$ROOT/assets/icon-512.png")
fi
"$AIB_BIN" build \
    -p "$ROOT" \
    --name appimage-builder \
    --version 0.1.0 \
    --entry-point "appimage_builder.__main__:main" \
    --gui-entry-point "appimage_builder.gui.main:main" \
    --build-type python \
    --output "$APPIMAGE_OUTPUT" \
    --linuxdeploy "$LINUXDEPLOY" \
    --appimagetool "$APPIMAGETOOL" \
    "${ICON_ARGS[@]}" \
    "${EXCLUDE_ARGS[@]}"

printf '[build-appimage] OK: %s\n' "$APPIMAGE_OUTPUT"
ls -la "$APPIMAGE_OUTPUT"
