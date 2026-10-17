"""Carga dinamica de idiomas (§57). Agregar idioma = anadir lang_xx.json."""
import json
from pathlib import Path

LANG_DIR = Path(__file__).resolve().parent / "lang"
DEFAULT = "es"


class I18n:
    def __init__(self, default: str = DEFAULT) -> None:
        self._lang = default
        self._tables: dict[str, dict[str, str]] = {}
        self._load(default)
        if default != "en":
            self._load("en")

    def _load(self, code: str) -> None:
        p = LANG_DIR / f"lang_{code}.json"
        if p.exists():
            self._tables[code] = json.loads(p.read_text(encoding="utf-8"))
        else:
            self._tables[code] = {}

    def set_language(self, code: str) -> None:
        if code not in self._tables:
            self._load(code)
        self._lang = code

    def language(self) -> str:
        return self._lang

    def t(self, key: str) -> str:
        # Fallback: idioma actual -> es -> clave.
        for code in (self._lang, DEFAULT):
            v = self._tables.get(code, {}).get(key)
            if v:
                return v
        return key
