"""Configuración de logging para Mod_Maker.

Norma §18: niveles coherentes (DEBUG, INFO, WARNING, ERROR, CRITICAL).
Nunca registrar secretos deliberadamente.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".mod_maker" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "mod_maker.log"

logger = logging.getLogger("mod_maker")
logger.setLevel(logging.DEBUG)

# Evitar duplicar handlers si el módulo se importa varias veces
if not logger.handlers:
    # Handler de archivo
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Handler de consola (solo INFO en adelante)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger hijo con el nombre dado."""
    return logger.getChild(name)
