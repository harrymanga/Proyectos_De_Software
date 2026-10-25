#!/bin/sh
# Compila MojoSetup para ARM64 y lo deja en data/vendor/mojosetup-arm64/.
# Hace falta un toolchain aarch64 (no viene en un x86 normal):
#
#   Debian/Ubuntu:
#     sudo apt install gcc-aarch64-linux-gnu libc6-dev-arm64-cross
#     scripts/build_mojosetup_arm64.sh /usr/bin/aarch64-linux-gnu-gcc
#
#   Fedora:
#     sudo dnf install gcc-aarch64-linux-gnu glibc-devel-arm64
#
# Los binarios ARM64 son un artefacto aparte: la app usa data/vendor/mojosetup/
# para el host y este directorio para preparar un paquete multi-arch.
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
WORK="$ROOT/.build/mojosetup-arm64"
OUT="$ROOT/data/vendor/mojosetup-arm64"
COMMIT="abbf8bc026bf3155783389e6a72fafad19d5dacd"
CC="${1:-aarch64-linux-gnu-gcc}"

command -v cmake >/dev/null 2>&1 || { echo "Falta cmake"; exit 1; }
if ! command -v "$CC" >/dev/null 2>&1; then
  echo "Falta el cross-compiler: $CC"
  echo "Instálalo o pásalo como primer argumento."
  exit 1
fi

mkdir -p "$WORK"
if [ ! -d "$WORK/mojosetup/.git" ]; then
  git clone https://github.com/icculus/mojosetup.git "$WORK/mojosetup"
fi
git -C "$WORK/mojosetup" checkout --quiet "$COMMIT"

rm -rf "$WORK/mojosetup/build"
mkdir -p "$WORK/mojosetup/build"
cd "$WORK/mojosetup/build"
cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -DCMAKE_SYSTEM_NAME=Linux \
      -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
      -DCMAKE_C_COMPILER="$CC" \
      -DCMAKE_BUILD_TYPE=MinSizeRel \
      -DMOJOSETUP_GUI_NCURSES=OFF \
      -DMOJOSETUP_GUI_GTKPLUS2=OFF \
      -DMOJOSETUP_GUI_GTKPLUS3=OFF \
      -DMOJOSETUP_GUI_COCOA=OFF .. > /dev/null
make -j"$(nproc 2>/dev/null || echo 2)" > /dev/null

mkdir -p "$OUT/scripts"
cp "$WORK/mojosetup/build/mojosetup" "$OUT/mojosetup"
cp "$WORK/mojosetup/build/make_self_extracting" "$OUT/make_self_extracting"
cp "$WORK/mojosetup/scripts/mojosetup_init.lua" "$OUT/scripts/"
cp "$WORK/mojosetup/scripts/mojosetup_mainline.lua" "$OUT/scripts/"
cp "$WORK/mojosetup/scripts/localization.lua" "$OUT/scripts/"
cp "$WORK/mojosetup/LICENSE.txt" "$OUT/LICENSE.txt"
chmod +x "$OUT/mojosetup"

file "$OUT/mojosetup"
echo "Listo: $OUT"