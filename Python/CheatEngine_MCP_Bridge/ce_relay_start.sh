#!/bin/bash
# CE MCP TCP Relay - Usa el mismo wine que CE (GE-Proton11-1)
# Uso: ./ce_relay_start.sh

PROTON_DIR="$HOME/.local/share/lutris/runners/wine/GE-Proton11-1/files"
export WINEPREFIX="$HOME/.wine"

WINE_BIN="$PROTON_DIR/bin/wine"
WINE_SERVER="$PROTON_DIR/bin/wineserver"

RELAY_SCRIPT="/run/media/handerson/0CD2ACE7D2ACD66C/Carreras/Programacion/GitHub/Proyectos_De_Software/Python/CheatEngine_MCP_Bridge/MCP_Server/ce_tcp_relay.py"

HOST="${CE_MCP_HOST:-127.0.0.1}"
PORT="${CE_MCP_PORT:-9876}"

echo "[CE Relay] Wine: $WINE_BIN"
echo "[CE Relay] Prefix: $WINEPREFIX"
echo "[CE Relay] Listening on $HOST:$PORT"
echo "[CE Relay] Forwarding to: \\\\.\\pipe\\CE_MCP_Bridge_v99"
echo ""

exec "$WINE_BIN" python "$RELAY_SCRIPT" --host "$HOST" --port "$PORT"
