"""Descarga de thumbnails con sesión compartida + logging."""
from __future__ import annotations

import os
import urllib.parse
from pathlib import Path
from typing import Optional

import requests

from core import logger as log
from core.cache import exists, get_cache_path, save
from core.http import get_session

TIMEOUT = 10


def download(url: str | None, custom_path: str | Path | None = None) -> Optional[str]:
    if not url:
        return None

    if custom_path:
        filename = Path(urllib.parse.urlparse(url).path).name or "thumb.png"
        decoded = urllib.parse.unquote(filename)
        custom_file = Path(str(custom_path)) / decoded
        if custom_file.exists():
            return str(custom_file)
        try:
            r = get_session().get(url, timeout=TIMEOUT)
            r.raise_for_status()
            custom_file.parent.mkdir(parents=True, exist_ok=True)
            custom_file.write_bytes(r.content)
            return str(custom_file)
        except requests.RequestException as e:
            log.error(f"Error descargando {url}: {e}")
            return None
        except OSError as e:
            log.error(f"Error guardando {custom_file}: {e}")
            return None

    if exists(url):
        return get_cache_path(url)

    try:
        r = get_session().get(url, timeout=TIMEOUT)
        r.raise_for_status()
        save(url, r.content)
        return get_cache_path(url)
    except requests.RequestException as e:
        log.error(f"Error descargando {url}: {e}")
        return None
