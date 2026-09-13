#!/usr/bin/env bash
# ce_bridge.sh — lanzador unificado del CheatEngine MCP Bridge.
#
# Uso:
#   ./ce_bridge.sh [--transport pipe|tcp] [--host H] [--port P] [--role server|relay|all]
#
# Roles:
#   server  arranca MCP_Server/mcp_cheatengine.py (default)
#   relay   arranca MCP_Server/ce_tcp_relay.py vía wine (solo Windows/wine)
#   all     relay en fondo + servidor en primer plano (solo tcp)
#
# Env:
#   PYTHON    intérprete con deps (default: ./venv/bin/python)
#   WINE_BIN  binario wine para el relay (default: wine)
#   CE_MCP_HOST / CE_MCP_PORT / CE_MCP_TRANSPORT (tienen prioridad los flags)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSPORT="${CE_MCP_TRANSPORT:-pipe}"
HOST="${CE_MCP_HOST:-127.0.0.1}"
PORT="${CE_MCP_PORT:-9876}"
ROLE="server"
WINE_BIN="${WINE_BIN:-wine}"
PYTHON="${PYTHON:-"$SCRIPT_DIR/venv/bin/python"}"

usage() {
  sed -n '2,15p' "$0"
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --transport) TRANSPORT="$2"; shift 2 ;;
    --transport=*) TRANSPORT="${1#*=}"; shift ;;
    --host) HOST="$2"; shift 2 ;;
    --host=*) HOST="${1#*=}"; shift ;;
    --port) PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --role) ROLE="$2"; shift 2 ;;
    --role=*) ROLE="${1#*=}"; shift ;;
    -h|--help) usage 0 ;;
    *) echo "Opción desconocida: $1" >&2; usage 2 ;;
  esac
done

case "$TRANSPORT" in
  pipe|tcp) ;;
  *) echo "ERROR: --transport debe ser 'pipe' o 'tcp'." >&2; exit 2 ;;
esac

case "$ROLE" in
  server|relay|all) ;;
  *) echo "ERROR: --role debe ser 'server', 'relay' o 'all'." >&2; exit 2 ;;
esac

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 1 || "$PORT" -gt 65535 ]]; then
  echo "ERROR: --port debe estar entre 1 y 65535." >&2
  exit 2
fi

SERVER_PY="$SCRIPT_DIR/MCP_Server/mcp_cheatengine.py"
RELAY_PY="$SCRIPT_DIR/MCP_Server/ce_tcp_relay.py"
[[ -f "$SERVER_PY" ]] || { echo "ERROR: no existe $SERVER_PY" >&2; exit 1; }
[[ -f "$RELAY_PY" ]] || { echo "ERROR: no existe $RELAY_PY" >&2; exit 1; }
[[ -x "$PYTHON" ]] || { echo "ERROR: intérprete no ejecutable: $PYTHON (crea ./venv o exporta PYTHON=...)" >&2; exit 1; }

start_server() {
  echo "[bridge] server transport=$TRANSPORT host=$HOST port=$PORT" >&2
  CE_MCP_TRANSPORT="$TRANSPORT" CE_MCP_HOST="$HOST" CE_MCP_PORT="$PORT" \
    exec "$PYTHON" "$SERVER_PY"
}

start_relay() {
  command -v "$WINE_BIN" >/dev/null 2>&1 || { echo "ERROR: wine no encontrado: $WINE_BIN (exporta WINE_BIN=...)" >&2; exit 1; }
  echo "[bridge] relay $HOST:$PORT -> \\\\.\\pipe\\CE_MCP_Bridge_v99 (wine: $WINE_BIN)" >&2
  exec "$WINE_BIN" "$PYTHON" "$RELAY_PY" --host "$HOST" --port "$PORT"
}

if [[ "$ROLE" == "server" ]]; then
  start_server
elif [[ "$ROLE" == "relay" ]]; then
  start_relay
else
  [[ "$TRANSPORT" == "tcp" ]] || { echo "ERROR: --role all requiere --transport tcp." >&2; exit 2; }
  command -v "$WINE_BIN" >/dev/null 2>&1 || { echo "ERROR: wine no encontrado: $WINE_BIN" >&2; exit 1; }
  echo "[bridge] relay en fondo + server en primer plano" >&2
  "$WINE_BIN" "$PYTHON" "$RELAY_PY" --host "$HOST" --port "$PORT" &
  RELAY_PID=$!
  trap 'kill "$RELAY_PID" 2>/dev/null || true' INT TERM EXIT
  CE_MCP_TRANSPORT="tcp" CE_MCP_HOST="$HOST" CE_MCP_PORT="$PORT" "$PYTHON" "$SERVER_PY"
fi
