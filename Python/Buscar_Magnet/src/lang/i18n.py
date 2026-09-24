"""Catálogo de idiomas en JSON separados (src/lang/lang_xx.json).

Agregar idioma = añadir un archivo. Cero cambios de código: los files
se descubren por glob y la key "lang.name" da el name a mostrar.
"""
import glob
import json
import os

LANG_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT = "es"


def _load():
    catalogs = {}
    for path in sorted(glob.glob(os.path.join(LANG_DIR, "lang_*.json"))):
        code = os.path.basename(path)[5:-5]
        try:
            with open(path, encoding="utf-8") as f:
                catalogs[code] = json.load(f)
        except (OSError, ValueError):
            continue
    return catalogs


STRINGS = _load()


def system_language():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        code = (os.environ.get(var, "")[:2]).lower()
        if code in STRINGS:
            return code
    return DEFAULT


class Language:
    """Catálogo activo con fallback al español."""

    def __init__(self, code=""):
        self.current = code if code in STRINGS else system_language()

    def available(self):
        return sorted(STRINGS)

    def name(self, code):
        return STRINGS.get(code, {}).get("lang.name", code)

    def set(self, code):
        if code not in STRINGS:
            return False
        self.current = code
        return True

    def tr(self, key, **kwargs):
        text = STRINGS.get(self.current, {}).get(key)
        if text is None:
            text = STRINGS.get(DEFAULT, {}).get(key, key)
        try:
            return text.format(**kwargs) if kwargs else text
        except (KeyError, IndexError):
            return text
