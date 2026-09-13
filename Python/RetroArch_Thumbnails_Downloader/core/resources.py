"""Rutas a recursos (dev + PyInstaller + AppImage) y a dirs escribibles."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_SLUG = "retro-thumbnails"


def get_resource_path(relative_path: str | Path) -> Path:
    """Devuelve ruta absoluta a un recurso de solo lectura.

    - En ejecutable PyInstaller usa ``sys._MEIPASS``.
    - Instalado (pip/AppImage): junto al paquete ``core/`` en site-packages.
    - En desarrollo: la raíz del proyecto (padre de ``core/``).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / str(relative_path)
    project_root = Path(__file__).resolve().parent.parent
    return project_root / str(relative_path)


def get_writable_dir(*parts: str) -> Path:
    """Dir escribible por usuario (nunca dentro del paquete/AppImage).

    Respeta ``XDG_CACHE_HOME`` (o ``~/.cache``) y ``RETRO_THUMB_CACHE`` como raíz.
    """
    root = os.environ.get("RETRO_THUMB_CACHE") or os.environ.get("XDG_CACHE_HOME") or str(
        Path.home() / ".cache"
    )
    path = Path(root) / APP_SLUG / Path(*parts) if parts else Path(root) / APP_SLUG
    path.mkdir(parents=True, exist_ok=True)
    return path
