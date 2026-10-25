"""Configuración global de pytest para Mod_Maker."""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que src/ sea importable
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
