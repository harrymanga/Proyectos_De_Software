#!/usr/bin/env bash
# Compat: servidor MCP con transporte TCP 127.0.0.1:9876.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/ce_bridge.sh" --role server --transport tcp --host 127.0.0.1 --port 9876
