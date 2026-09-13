#!/usr/bin/env bash
# Relay TCP->pipe vía wine. Configurable con WINE_BIN, CE_MCP_HOST, CE_MCP_PORT.
# Compat: delega en ce_bridge.sh (nuevo lanzador unificado).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/ce_bridge.sh" --role relay \
  --host "${CE_MCP_HOST:-127.0.0.1}" --port "${CE_MCP_PORT:-9876}"
