#!/bin/bash
# Compara el upstream fijado contra una versión nueva: lista .gd/.tscn
# añadidos, eliminados y modificados en standalone/ para re-extraer cadenas.
# Uso: bash verificar_actualizacion.sh --actual <DIR_VIEJO> --nuevo <DIR_NUEVO>
set -euo pipefail
ACTUAL=""; NUEVO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --actual) ACTUAL="$2"; shift 2;;
    --nuevo) NUEVO="$2"; shift 2;;
    *) echo "Uso: $0 --actual <DIR> --nuevo <DIR>" >&2; exit 1;;
  esac
done
[ -n "$ACTUAL" ] && [ -n "$NUEVO" ] || { echo "Faltan argumentos." >&2; exit 1; }
echo "== Añadidos =="
comm -13 <(cd "$ACTUAL/standalone" && find . -name '*.gd' -o -name '*.tscn' | sort) <(cd "$NUEVO/standalone" && find . -name '*.gd' -o -name '*.tscn' | sort) || true
echo "== Eliminados =="
comm -23 <(cd "$ACTUAL/standalone" && find . -name '*.gd' -o -name '*.tscn' | sort) <(cd "$NUEVO/standalone" && find . -name '*.gd' -o -name '*.tscn' | sort) || true
echo "== Modificados (mtime/tamaño) =="
diff -rq "$ACTUAL/standalone" "$NUEVO/standalone" 2>/dev/null | grep -E '\.gd$|\.tscn$' || echo "(sin cambios en .gd/.tscn)"
echo "== Siguiente paso =="
echo "python3 tools/extraer_cadenas.py --upstream $NUEVO --out locale/plantilla_nueva.csv"
