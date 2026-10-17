#!/usr/bin/env bash
# Lanzador sin friccion (§56): crea .venv, instala deps y ejecuta.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV"
fi
"$PY" -m pip install --upgrade pip -q
"$PY" -m pip install -r "$ROOT/requirements.txt"

exec "$PY" "$ROOT/src/main.py" "$@"
