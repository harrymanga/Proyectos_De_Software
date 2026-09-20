"""Gestor de idioma de la interfaz (extensible).

Detecta automáticamente los módulos de `locales/` que definan
LANGUAGE_CODE, LANGUAGE_NAME y STRINGS. Agregar un idioma = añadir un
archivo (sin tocar este gestor ni la GUI).
"""
import importlib
import pkgutil
from typing import Dict, List

from traductor_pro.infrastructure.localization import locales

DEFAULT_LANGUAGE = "es"


class LanguageManager:
    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self._catalogs: Dict[str, Dict[str, str]] = {}
        self._names: Dict[str, str] = {}
        self._load()
        self._current = language if language in self._catalogs else DEFAULT_LANGUAGE

    def _load(self) -> None:
        for info in pkgutil.iter_modules(locales.__path__):
            module = importlib.import_module(f"{locales.__name__}.{info.name}")
            code = getattr(module, "LANGUAGE_CODE", None)
            if not code:
                continue
            self._catalogs[code] = dict(getattr(module, "STRINGS", {}))
            self._names[code] = getattr(module, "LANGUAGE_NAME", code)

    @property
    def current(self) -> str:
        return self._current

    def available(self) -> List[str]:
        return sorted(self._catalogs)

    def language_name(self, code: str) -> str:
        return self._names.get(code, code)

    def set_language(self, code: str) -> bool:
        if code not in self._catalogs:
            return False
        self._current = code
        return True

    def tr(self, key: str, **kwargs) -> str:
        text = self._catalogs.get(self._current, {}).get(key)
        if text is None:
            text = self._catalogs.get(DEFAULT_LANGUAGE, {}).get(key, key)
        try:
            return text.format(**kwargs) if kwargs else text
        except (KeyError, IndexError):
            return text
