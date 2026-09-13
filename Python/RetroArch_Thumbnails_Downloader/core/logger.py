"""Logging centralizado (sin efectos al importar salvo crear dir bajo demanda)."""
from __future__ import annotations

import logging
from pathlib import Path

from core.resources import get_writable_dir

_configured = False


def get_logger(name: str = "retro_thumbnails") -> logging.Logger:
    global _configured
    logger = logging.getLogger(name)
    if _configured:
        return logger
    try:
        log_dir = get_writable_dir("logs")
        handler_file: logging.Handler = logging.FileHandler(
            str(log_dir / "app.log"), encoding="utf-8"
        )
    except OSError:
        handler_file = logging.NullHandler()
    handler_stream = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler_file.setFormatter(fmt)
    handler_stream.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(handler_file)
        logger.addHandler(handler_stream)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    _configured = True
    return logger


def info(msg: str) -> None:
    get_logger().info(msg)


def error(msg: str) -> None:
    get_logger().error(msg)


def warning(msg: str) -> None:
    get_logger().warning(msg)


# Mantener comportamiento previo: logger raíz configurado de forma perezosa.
# No llamar a basicConfig con StreamHandler global para no duplicar salida en tests.
