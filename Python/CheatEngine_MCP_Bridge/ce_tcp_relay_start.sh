#!/usr/bin/env bash
# Compat: relay con valores clásicos 127.0.0.1:9876.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/ce_bridge.sh" --role relay --host 127.0.0.1 --port 9876
