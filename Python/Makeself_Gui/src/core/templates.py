"""Genera esqueletos archive_dir listos para empaquetar (console/zenity/mojosetup/universal)."""
from __future__ import annotations

import os

CONSOLE_SETUP = """#!/bin/sh
# Instalador consola generado por Makeself GUI (plantilla console).
set -e
cd "$(dirname "$0")"
echo "Instalando {label} en $1..."
mkdir -p "${{1:-$HOME/.local/share/{slug}}}"
cp -r data "${{1:-$HOME/.local/share/{slug}}}/" 2>/dev/null || cp -r . "${{1:-$HOME/.local/share/{slug}}}/"
echo "Listo."
"""

ZENITY_SETUP = """#!/bin/sh
# Instalador gráfico Zenity generado por Makeself GUI (plantilla zenity).
set -e
cd "$(dirname "$0")"
DEST=$(zenity --file-selection --directory --title="Destino de {label}" 2>/dev/null || echo "$HOME/.local/share/{slug}")
mkdir -p "$DEST"
cp -r . "$DEST/" | (zenity --progress --pulsate --title="{label}" --text="Copiando…" --auto-close 2>/dev/null || cat)
zenity --info --text="{label}: instalado en $DEST" 2>/dev/null || echo "Instalado en $DEST"
"""

MOJO_README = """# Plantilla estilo MojoSetup/GOG (simplificada)
# Estructura generada:
#   startmojo.sh  -> punto de entrada que lanza el instalador real
#   scripts/config.lua -> metadatos del paquete
#   data/         -> coloca aquí los archivos del juego
# El .run final se crea con startup_script=./startmojo.sh.
# El instalador GOG real usa el binario mojosetup; aquí se usa un stub shell
# compatible para que el flujo Crear/Inspeccionar funcione sin binarios externos.
"""

MOJO_START = """#!/bin/sh
# Stub estilo startmojo.sh (plantilla mojosetup simplificada).
set -e
cd "$(dirname "$0")"
echo "== {label} =="
echo "Instalando data/ en ${{1:-./{slug}-installed}} ..."
mkdir -p "${{1:-./{slug}-installed}}"
cp -r data "${{1:-./{slug}-installed}}/" 2>/dev/null || true
cat scripts/config.lua 2>/dev/null || true
echo "Instalación terminada."
"""

MOJO_LUA = """-- Metadatos estilo MojoSetup (plantilla simplificada)
Setup = Setup or {{}}
Setup.Package = {{
  vendor = "Makeself GUI",
  id = "{slug}",
  description = "{label}",
  version = "1.0",
}}
"""

TEMPLATES = ("console", "zenity", "mojosetup", "universal", "graphical")

UNIVERSAL_SETUP = """#!/bin/sh
# Instalador universal Makeself GUI — sirve para juegos y programas.
# Convención: si ./data/ existe y NO está vacía, instala su contenido;
# si no, instala todo el archive excepto setup.sh y *.msgui.json.
# Uso: ./setup.sh [DESTINO] [--link] [--desktop] | --list | --help
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="{label}"
APP_SLUG="{slug}"
DEST=""
DO_LINK="n"
DO_DESKTOP="n"
END_OPTS="n"
for arg in "$@"; do
  if [ "$END_OPTS" = "y" ]; then DEST="$arg"; continue; fi
  case "$arg" in
    --) END_OPTS="y";;
    --help|-h) echo "Uso: ./setup.sh [DESTINO] [--link] [--desktop] | --list | --help";
      echo "Defecto: $HOME/.local/share/$APP_SLUG"; exit 0;;
    --list) echo "Contenido a instalar:"; ls -1 "$SRC"; exit 0;;
    --link) DO_LINK="y";;
    --desktop) DO_DESKTOP="y";;
    --*) echo "Opción desconocida: $arg" >&2; exit 1;;
    *) DEST="$arg";;
  esac
done
[ -z "$DEST" ] && DEST="$HOME/.local/share/$APP_SLUG"

need_kb() {{
  if [ -d "$SRC/data" ] && [ -n "$(ls -A -- "$SRC/data")" ]; then du -sk -- "$SRC/data" | cut -f1;
  else du -sk -- "$SRC" | cut -f1; fi
}}

free_kb() {{
  df -k -- "$1" | tail -n 1 | awk '{{print $4}}'
}}

mkdir -p -- "$DEST"
NEED="$(need_kb)"; FREE="$(free_kb "$DEST")"
if [ "$FREE" -lt "$NEED" ]; then
  echo "Sin espacio en $DEST (libre $FREE KB, necesario $NEED KB). Elige otra carpeta o libera espacio." >&2
  exit 1
fi
if [ -d "$SRC/data" ] && [ -n "$(ls -A -- "$SRC/data")" ]; then
  cp -r -- "$SRC/data/." "$DEST/"
else
  for entry in "$SRC"/* "$SRC"/.[!.]*; do
    base="$(basename -- "$entry")"
    case "$base" in setup.sh|proyecto.msgui.json) continue;; esac
    [ -e "$entry" ] || continue
    cp -r -- "$entry" "$DEST/"
  done
fi
LAUNCHER=""
for candidate in "$DEST/start.sh" "$DEST/startmojo.sh" "$DEST/AppRun"; do
  if [ -f "$candidate" ]; then LAUNCHER="$candidate"; break; fi
done
if [ -z "$LAUNCHER" ]; then
  LAUNCHER="$(find "$DEST" -maxdepth 3 -type f -perm -u+x ! -name '*.so*' ! -name '*.sh' | head -n 1)"
fi
[ -n "$LAUNCHER" ] && chmod +x -- "$LAUNCHER" 2>/dev/null || true
cat > "$DEST/uninstall.sh" <<EOF
#!/bin/sh
set -e
echo "Desinstalando $APP_NAME de $DEST..."
rm -rf -- "$DEST"
rm -f -- "\\$HOME/.local/bin/$APP_SLUG" "\\$HOME/.local/share/applications/$APP_SLUG.desktop"
echo "Listo."
EOF
chmod +x -- "$DEST/uninstall.sh"
if [ "$DO_LINK" = "y" ] && [ -n "$LAUNCHER" ]; then
  mkdir -p -- "$HOME/.local/bin"
  ln -sf -- "$LAUNCHER" "$HOME/.local/bin/$APP_SLUG"
fi
if [ "$DO_DESKTOP" = "y" ] && [ -n "$LAUNCHER" ]; then
  mkdir -p -- "$HOME/.local/share/applications"
  printf '[Desktop Entry]\\nType=Application\\nName=%s\\nExec="%s"\\nTerminal=false\\nCategories=Game;\\n' \\
    "$APP_NAME" "$LAUNCHER" > "$HOME/.local/share/applications/$APP_SLUG.desktop"
fi
echo "$APP_NAME instalado en $DEST."
if [ -n "$LAUNCHER" ]; then echo "Ejecutable: $LAUNCHER"; fi
exit 0
"""

GRAPHICAL_SETUP = """#!/bin/sh
# Instalador gráfico Makeself GUI (plantilla graphical).
# Con DISPLAY y zenity: asistente (info, destino, progreso %, accesos, ejecutar).
# Sin GUI o con --nogui: modo consola.
# Uso: ./setup.sh [DESTINO] [--link] [--desktop] [--nogui] [--skip-verify] | --list | --help
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="{label}"
APP_SLUG="{slug}"
DEST=""
DO_LINK="n"
DO_DESKTOP="n"
END_OPTS="n"
GUI_MODE="auto"
SKIP_VERIFY="n"
for arg in "$@"; do
  if [ "$END_OPTS" = "y" ]; then DEST="$arg"; continue; fi
  case "$arg" in
    --) END_OPTS="y";;
    --help|-h)
      echo "Uso: ./setup.sh [DESTINO] [--link] [--desktop] [--nogui] [--skip-verify] | --list | --help";
      echo "Defecto: $HOME/.local/share/$APP_SLUG"; exit 0;;
    --list) echo "Contenido a instalar:"; ls -1 -- "$SRC"; exit 0;;
    --link) DO_LINK="y";;
    --desktop) DO_DESKTOP="y";;
    --nogui) GUI_MODE="no";;
    --skip-verify) SKIP_VERIFY="y";;
    --*) echo "Opción desconocida: $arg" >&2; exit 1;;
    *) DEST="$arg";;
  esac
done
[ -z "$DEST" ] && DEST="$HOME/.local/share/$APP_SLUG"

has_gui() {{
  [ "$GUI_MODE" = "no" ] && return 1
  [ -n "${{DISPLAY:-}}" ] && command -v zenity >/dev/null 2>&1
}}

use_data() {{
  [ -d "$SRC/data" ] && [ -n "$(ls -A -- "$SRC/data")" ]
}}

payload_total() {{
  if use_data; then find "$SRC/data" -type f | wc -l | tr -d ' ';
  else find "$SRC" -type f ! -name setup.sh ! -name proyecto.msgui.json | wc -l | tr -d ' '; fi
}}

need_kb() {{
  if use_data; then du -sk -- "$SRC/data" | cut -f1;
  else du -sk -- "$SRC" | cut -f1; fi
}}

free_kb() {{
  df -k -- "$1" | tail -n 1 | awk '{{print $4}}'
}}

ensure_space_console() {{
  mkdir -p -- "$DEST"
  NEED="$(need_kb)"; FREE="$(free_kb "$DEST")"
  if [ "$FREE" -lt "$NEED" ]; then
    echo "Sin espacio en $DEST (libre $FREE KB, necesario $NEED KB). Elige otra carpeta o libera espacio." >&2
    return 1
  fi
}}

find_launcher_in() {{
  _base="$1"
  for candidate in "$_base/start.sh" "$_base/startmojo.sh" "$_base/AppRun"; do
    if [ -f "$candidate" ]; then echo "$candidate"; return 0; fi
  done
  find "$_base" -maxdepth 3 -type f -perm -u+x ! -name '*.so*' ! -name '*.sh' | head -n 1
}}

write_uninstaller() {{
  _dest="$1"
  cat > "$_dest/uninstall.sh" <<EOF
#!/bin/sh
set -e
echo "Desinstalando $APP_NAME de $_dest..."
rm -rf -- "$_dest"
rm -f -- "\\$HOME/.local/bin/$APP_SLUG" "\\$HOME/.local/share/applications/$APP_SLUG.desktop"
echo "Listo."
EOF
  chmod +x -- "$_dest/uninstall.sh"
}}

finish_links() {{
  _launcher="$1"
  [ -n "$_launcher" ] || return 0
  chmod +x -- "$_launcher" 2>/dev/null || true
  if [ "$DO_LINK" = "y" ]; then
    mkdir -p -- "$HOME/.local/bin"
    ln -sf -- "$_launcher" "$HOME/.local/bin/$APP_SLUG"
  fi
  if [ "$DO_DESKTOP" = "y" ]; then
    mkdir -p -- "$HOME/.local/share/applications"
    printf '[Desktop Entry]\\nType=Application\\nName=%s\\nExec="%s"\\nTerminal=false\\nCategories=Game;\\n' \\
      "$APP_NAME" "$_launcher" > "$HOME/.local/share/applications/$APP_SLUG.desktop"
  fi
}}

copy_console() {{
  _dest="$1"
  mkdir -p -- "$_dest"
  if use_data; then
    cp -r -- "$SRC/data/." "$_dest/"
  else
    for entry in "$SRC"/* "$SRC"/.[!.]*; do
      base="$(basename -- "$entry")"
      case "$base" in setup.sh|proyecto.msgui.json) continue;; esac
      [ -e "$entry" ] || continue
      cp -r -- "$entry" "$_dest/"
    done
  fi
}}

copy_with_progress() {{
  _dest="$1"; _total="$2"; _count=0
  mkdir -p -- "$_dest"
  if use_data; then _from="$SRC/data"; else _from="$SRC"; fi
  ( cd -- "$_from" && tar cf - --exclude=./setup.sh --exclude=./proyecto.msgui.json . 2>/dev/null \\
    | tar xvf - -C "$_dest" 2>/dev/null ) | while IFS= read -r _line; do
    _count=$((_count+1))
    _pct=$((_count*100/_total))
    [ "$_pct" -gt 100 ] && _pct=100
    echo "$_pct"
  done
  echo 100
}}

payload_info() {{
  _size="$(du -sh -- "$SRC" | cut -f1)"
  _n="$(payload_total)"
  _exe="$(find_launcher_in "$SRC")"
  if [ -n "$_exe" ]; then _exe="Ejecutable: $(basename -- "$_exe")";
  else _exe="Ejecutable: (no detectado)"; fi
  printf '%s\\nTamano: %s | Archivos: %s\\n%s\\n%s.' \\
    "$APP_NAME" "$_size" "$_n" "$_exe" "$VERIFY_SUMMARY"
}}

find_run_path() {{
  if [ -r /proc/$PPID/cmdline ] 2>/dev/null; then
    _pcwd="$(readlink /proc/$PPID/cwd 2>/dev/null)"
    tr '\\0' '\\n' < /proc/$PPID/cmdline 2>/dev/null | while IFS= read -r _w; do
      case "$_w" in *.run|*.sh)
        for _cand in "$_w" "$_pcwd/$_w"; do
          if [ -f "$_cand" ] && [ ! "$_cand" -ef "$0" ] && grep -qa "Makeself" "$_cand" 2>/dev/null; then
            echo "$_cand"; break
          fi
        done;;
      esac
    done | head -n 1
  fi
  return 0
}}

run_package_check() {{
  _run="$1"; _tmpout="$(mktemp)"
  sh "$_run" --check >"$_tmpout" 2>&1 &
  _pid=$!
  if ( while kill -0 "$_pid" 2>/dev/null; do
         _p="$(tail -c 500 "$_tmpout" 2>/dev/null | tr '\\b\\r' '\\n' | grep -ao '[0-9][0-9]*%' | tail -n 1 | tr -dc '0-9')"
         [ -n "$_p" ] && echo "$_p"
         sleep 1
       done; echo 100 ) | zenity --progress --title="$APP_NAME" --text="Verificando integridad" --percentage=0 --auto-close; then
    :
  else
    kill "$_pid" 2>/dev/null || true
    wait "$_pid" 2>/dev/null || true
    rm -f -- "$_tmpout"
    return 1
  fi
  _rc=0; wait "$_pid" || _rc=$?
  _out="$(cat -- "$_tmpout")"; rm -f -- "$_tmpout"
  printf '%s' "$_out"
  return "$_rc"
}}

console_install() {{
  ensure_space_console || exit 1
  copy_console "$DEST"
  LAUNCHER="$(find_launcher_in "$DEST")"
  write_uninstaller "$DEST"
  finish_links "$LAUNCHER"
  echo "$APP_NAME instalado en $DEST."
  if [ -n "$LAUNCHER" ]; then echo "Ejecutable: $LAUNCHER"; fi
  exit 0
}}

gui_install() {{
  VERIFY_SUMMARY="Integridad verificada al extraer (SHA256/MD5)."
  if [ "$SKIP_VERIFY" != "y" ]; then
    _run_path="$(find_run_path)"
    if [ -n "$_run_path" ]; then
      if _check_out="$(run_package_check "$_run_path")"; then
        _sum="$(printf '%s' "$_check_out" | tr '\\b\\r' '\\n' | grep -a 'checksums are OK\\|All good\\|FAILED\\|ERROR' | tail -n 4 | tr '\\n' ' ' | tr -s ' ')"
        [ -n "$_sum" ] && VERIFY_SUMMARY="$_sum"
      else
        zenity --error --title="$APP_NAME" --text="La verificacion del paquete fallo. No se instalara." || true
        exit 1
      fi
    fi
  fi
  zenity --info --title="$APP_NAME" --width=440 --text="$(payload_info)" || exit 1
  CHOSEN="$(zenity --file-selection --directory --title="Destino de $APP_NAME" --filename="$DEST/")" || exit 1
  [ -n "$CHOSEN" ] && DEST="$CHOSEN"
  zenity --question --title="$APP_NAME" --text="Instalar en: $DEST" || exit 1
  mkdir -p -- "$DEST"
  NEED="$(need_kb)"; FREE="$(free_kb "$DEST")"
  while [ "$FREE" -lt "$NEED" ]; do
    zenity --error --title="$APP_NAME" --text="Sin espacio en $DEST (libre $FREE KB, necesario $NEED KB). Elige otra carpeta." || exit 1
    CHOSEN="$(zenity --file-selection --directory --title="Destino de $APP_NAME" --filename="$DEST/")" || exit 1
    [ -n "$CHOSEN" ] && DEST="$CHOSEN"
    mkdir -p -- "$DEST"
    FREE="$(free_kb "$DEST")"
  done
  TOTAL="$(payload_total)"
  [ "$TOTAL" -gt 0 ] || TOTAL=1
  copy_with_progress "$DEST" "$TOTAL" \\
    | zenity --progress --title="$APP_NAME" --text="Instalando" --percentage=0 --auto-close || exit 1
  rm -f -- "$DEST/setup.sh" "$DEST/proyecto.msgui.json"
  if [ -z "$(ls -A -- "$DEST")" ]; then
    zenity --error --title="$APP_NAME" --text="La copia no produjo archivos." || true
    exit 1
  fi
  LAUNCHER="$(find_launcher_in "$DEST")"
  write_uninstaller "$DEST"
  if [ "$DO_LINK" != "y" ]; then
    if zenity --question --title="$APP_NAME" --text="Crear comando en ~/.local/bin/$APP_SLUG?"; then DO_LINK="y"; fi
  fi
  if [ "$DO_DESKTOP" != "y" ]; then
    if zenity --question --title="$APP_NAME" --text="Crear acceso en el menu de aplicaciones?"; then DO_DESKTOP="y"; fi
  fi
  finish_links "$LAUNCHER"
  if [ -n "$LAUNCHER" ]; then
    if zenity --question --title="$APP_NAME" --text="Instalado en $DEST. Ejecutar ahora?"; then
      nohup "$LAUNCHER" </dev/null >/dev/null 2>&1 &
      exit 0
    fi
  fi
  zenity --info --title="$APP_NAME" --text="Instalado en $DEST."
}}

if has_gui; then gui_install; else console_install; fi
"""

GRAPHICAL_README = """# Plantilla graphical (asistente de instalación)
# - Con DISPLAY + zenity: info, destino, progreso %, accesos, ejecutar.
# - Sin GUI o con --nogui: modo consola (igual que universal).
# - startup_script=./setup.sh
"""

UNIVERSAL_README = """# Plantilla universal
# - Coloca los archivos en data/ (recomendado) o directo en esta carpeta.
# - startup_script=./setup.sh
# - ./setup.sh --list (ver), ./setup.sh DESTINO --link --desktop (instalar).
"""


def slugify(label: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in label).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "miapp"


def generate_scaffold(template: str, dest: str, label: str = "Mi App 1.0") -> list[str]:
    if template not in TEMPLATES:
        raise ValueError(f"plantilla desconocida: {template}")
    slug = slugify(label)
    created: list[str] = []
    os.makedirs(os.path.join(dest, "data"), exist_ok=True)
    created.append("data/")
    if template == "console":
        path = os.path.join(dest, "setup.sh")
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONSOLE_SETUP.format(label=label, slug=slug))
        os.chmod(path, 0o755)
        created.append("setup.sh")
    elif template == "zenity":
        path = os.path.join(dest, "setup.sh")
        with open(path, "w", encoding="utf-8") as f:
            f.write(ZENITY_SETUP.format(label=label, slug=slug))
        os.chmod(path, 0o755)
        created.append("setup.sh")
    elif template == "universal":
        for name, content in [
            ("setup.sh", UNIVERSAL_SETUP.format(label=label, slug=slug)),
            ("README.txt", UNIVERSAL_README),
        ]:
            path = os.path.join(dest, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            if name.endswith(".sh"):
                os.chmod(path, 0o755)
            created.append(name)
    elif template == "graphical":
        for name, content in [
            ("setup.sh", GRAPHICAL_SETUP.format(label=label, slug=slug)),
            ("README.txt", GRAPHICAL_README),
        ]:
            path = os.path.join(dest, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            if name.endswith(".sh"):
                os.chmod(path, 0o755)
            created.append(name)
    else:
        os.makedirs(os.path.join(dest, "scripts"), exist_ok=True)
        for name, content in [
            ("startmojo.sh", MOJO_START.format(label=label, slug=slug)),
            ("scripts/config.lua", MOJO_LUA.format(label=label, slug=slug)),
            ("README.txt", MOJO_README),
        ]:
            path = os.path.join(dest, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            if name.endswith(".sh"):
                os.chmod(path, 0o755)
            created.append(name)
    return created
