import hashlib
import os
from typing import Optional

from traductor_pro.domain.interfaces import CachePort
from traductor_pro.infrastructure.system.app_paths import default_cache_dir


class Md5Cache(CachePort):
    def __init__(self, cache_dir: str = "") -> None:
        if not cache_dir:
            cache_dir = default_cache_dir()
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)

    def get(self, key: str) -> Optional[str]:
        path = self._path(key)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def set(self, key: str, value: str) -> None:
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as f:
            f.write(value)

    def exists(self, key: str) -> bool:
        return os.path.isfile(self._path(key))

    def clear(self) -> None:
        for fname in os.listdir(self._cache_dir):
            fpath = os.path.join(self._cache_dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)

    def _path(self, key: str) -> str:
        hashed = hashlib.md5(key.encode("utf-8")).hexdigest()
        return os.path.join(self._cache_dir, f"{hashed}.txt")
