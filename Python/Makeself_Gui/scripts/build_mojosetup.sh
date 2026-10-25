#!/bin/sh
# Compila MojoSetup con los plugins GUI disponibles en el sistema.
# Uso: scripts/build_mojosetup.sh [--gui stdio|ncurses|gtk3|all]
# Por defecto: stdio + los que estén instalados. Sin deps de GUI: solo stdio.
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
WORK="$ROOT/.build/mojosetup"
VENDOR="$ROOT/data/vendor/mojosetup"
COMMIT="abbf8bc026bf3155783389e6a72fafad19d5dacd"
GUI_MODE="stdio"
if [ "${1:-}" = "--gui" ]; then
  GUI_MODE="${2:---help}"
fi

has() { command -v "$1" >/dev/null 2>&1; }
have_ncurses() { has pkg-config && pkg-config --exists ncurses; }
have_gtk3() { has pkg-config && pkg-config --exists gtk+-3.0; }

# Plugins GUI a compilar: "NO" desactiva, "STATIC" fuerza enlace estático.
# Por defecto SOLO stdio: evita que el instalador intente abrir una ventana
# gráfica (GTK/ncurses) y se quede colgado en pantallas sin DISPLAY.
GUI_NCURSES=NO
GUI_GTKPLUS3=NO
GUI_NCURSES_STATIC=FALSE
GUI_GTKPLUS3_STATIC=FALSE

case "$GUI_MODE" in
  stdio)
    ;;
  all)
    # "all" solo activa stdio. ncurses y GTK3 quedan excluidos a proposito
    # porque pueden hacer que el instalador entre en PANIC si no inicializan.
    ;;
  ncurses)
    GUI_NCURSES=ON; GUI_NCURSES_STATIC=TRUE
    echo "AVISO: ncurses puede causar problemas en terminales sin soporte completo."
    ;;
  gtk3)
    have_gtk3 || { echo "Falta gtk+-3.0 (instala libgtk-3-dev)"; exit 1; }
    echo "AVISO: el plugin Gtk3 puede hacer fallar el instalador en sistemas"
    echo "       sin Gtk3 o sin DISPLAY. Se empaqueta solo porque lo pediste."
    GUI_GTKPLUS3=ON; GUI_GTKPLUS3_STATIC=FALSE
    ;;
  *)
    echo "Uso: scripts/build_mojosetup.sh [--gui stdio|ncurses|gtk3|all]" >&2
    exit 1
    ;;
esac

command -v cmake >/dev/null 2>&1 || { echo "Falta cmake"; exit 1; }
command -v make  >/dev/null 2>&1 || { echo "Falta make"; exit 1; }

mkdir -p "$WORK"
if [ ! -d "$WORK/mojosetup/.git" ]; then
  git clone https://github.com/icculus/mojosetup.git "$WORK/mojosetup"
fi
git -C "$WORK/mojosetup" checkout --quiet "$COMMIT"

rm -rf "$WORK/mojosetup/build"
mkdir -p "$WORK/mojosetup/build"
cd "$WORK/mojosetup/build"
cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -DCMAKE_BUILD_TYPE=MinSizeRel \
      -DMOJOSETUP_GUI_STDIO=ON \
      -DMOJOSETUP_GUI_STDIO_STATIC=TRUE \
      -DMOJOSETUP_GUI_NCURSES="$GUI_NCURSES" \
      -DMOJOSETUP_GUI_NCURSES_STATIC="$GUI_NCURSES_STATIC" \
      -DMOJOSETUP_GUI_GTKPLUS3="$GUI_GTKPLUS3" \
      -DMOJOSETUP_GUI_GTKPLUS3_STATIC="$GUI_GTKPLUS3_STATIC" \
      -DMOJOSETUP_GUI_GTKPLUS2=OFF \
      -DMOJOSETUP_GUI_COCOA=OFF \
      -DMOJOSETUP_GUI_WWW=OFF .. > /dev/null
make -j"$(nproc 2>/dev/null || echo 2)" > /dev/null

# MojoSetup busca los plugins en guis/<arquitectura>/ junto al binario.
ARCH="$(uname -m)"
mkdir -p "$VENDOR/guis/$ARCH"
find "$WORK/mojosetup/build" -name "libmojosetupgui_*.so" -exec cp {} "$VENDOR/guis/$ARCH/" \; 2>/dev/null || true

mkdir -p "$VENDOR/scripts"
cp "$WORK/mojosetup/build/mojosetup" "$VENDOR/mojosetup"
cp "$WORK/mojosetup/build/make_self_extracting" "$VENDOR/make_self_extracting"
cp "$WORK/mojosetup/scripts/mojosetup_init.lua" "$VENDOR/scripts/"
cp "$WORK/mojosetup/scripts/mojosetup_mainline.lua" "$VENDOR/scripts/"
cp "$WORK/mojosetup/scripts/localization.lua" "$VENDOR/scripts/"
cp "$WORK/mojosetup/LICENSE.txt" "$VENDOR/LICENSE.txt"
chmod +x "$VENDOR/mojosetup"

echo "Listo: $VENDOR (gui=$GUI_MODE, arch=$ARCH)"
ls -la "$VENDOR" "$VENDOR/guis/$ARCH" 2>/dev/null