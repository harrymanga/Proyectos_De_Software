"""Caché local de thumbnails (md5 de URL, con TTL opcional)."""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Optional

from core.resources import get_writable_dir

# Dir escribible (~/.cache/retro-thumbnails/cache): nunca dentro del paquete,
# que en AppImage/pip es de solo lectura o no debe mutarse.
CACHE_DIR = str(get_writable_dir("cache"))
DEFAULT_TTL_SECONDS: Optional[int] = None  # sin expiración por defecto


def get_cache_path(url: str | None) -> Optional[str]:
    if not url:
        return None
    h = hashlib.md5(url.encode("utf-8")).hexdigest()
    return str(Path(str(CACHE_DIR)) / f"{h}.png")


def exists(url: str | None, ttl_seconds: Optional[int] = DEFAULT_TTL_SECONDS) -> bool:
    cache_path = get_cache_path(url)
    if not cache_path or not os.path.exists(cache_path):
        return False
    if ttl_seconds is not None:
        age = time.time() - os.path.getmtime(cache_path)
        if age > ttl_seconds:
            return False
    return True


def save(url: str | None, content: bytes | None) -> None:
    if not url or not content:
        return
    cache_path = get_cache_path(url)
    if not cache_path:
        return
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(content)
