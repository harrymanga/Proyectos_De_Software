#!/bin/sh
# Lanzador sin fricción: crea .venv, instala deps y ejecuta.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/pip install -q -r requirements.txt
exec .venv/bin/python src/app.py "$@"
