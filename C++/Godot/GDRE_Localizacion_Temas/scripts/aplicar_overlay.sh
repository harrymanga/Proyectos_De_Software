#!/bin/bash
# Aplica el overlay sobre una copia de trabajo del upstream (nunca el original).
# Uso: bash aplicar_overlay.sh --upstream <DIR> --destino <DIR>
set -euo pipefail
UPSTREAM=""; DESTINO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --upstream) UPSTREAM="$2"; shift 2;;
    --destino) DESTINO="$2"; shift 2;;
    *) echo "Uso: $0 --upstream <DIR> --destino <DIR>" >&2; exit 1;;
  esac
done
[ -n "$UPSTREAM" ] && [ -n "$DESTINO" ] || { echo "Faltan argumentos." >&2; exit 1; }
[ -f "$UPSTREAM/standalone/project.godot" ] || { echo "No parece upstream GDRE: $UPSTREAM" >&2; exit 1; }
mkdir -p "$DESTINO"
cp -r "$UPSTREAM/standalone" "$DESTINO/standalone-base"
mkdir -p "$DESTINO/overlay/locale" "$DESTINO/overlay/themes"
cp locale/*.csv "$DESTINO/overlay/locale/" 2>/dev/null || echo "Sin CSV todavía: genera con tools/extraer_cadenas.py"
python3 themes/generar_tema_claro.py --tema "$UPSTREAM/standalone/gdre_theme.tres" --out "$DESTINO/overlay/themes/gdre_theme_light.tres"
cat > "$DESTINO/LEEME_OVERLAY.txt" <<EOF
Overlay aplicado desde GDRE_Localizacion_Temas.
- standalone-base/: copia intacta del upstream (referencia).
- overlay/locale/: CSV es + futuros idiomas.
- overlay/themes/: tema claro generado.
Integración pendiente en el fork: cargar CSV vía TranslationServer y
conmutador de tema en gdre_main.gd (ver docs/ACTUALIZACIONES.md).
EOF
echo "Overlay aplicado en: $DESTINO"
