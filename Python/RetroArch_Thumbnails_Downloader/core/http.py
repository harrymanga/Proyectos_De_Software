"""Sesión HTTP compartida con reintentos."""
from __future__ import annotations

from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


@lru_cache(maxsize=1)
def get_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "RetroArch-Thumbnails-Downloader/2.0"})
    return session
