"""Carga dinámica de idiomas. Agregar un idioma = añadir src/lang/lang_xx.json."""
from __future__ import annotations

import json
import os

LANG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang")
DEFAULT_LANG = "es"
FALLBACK_LANG = "en"

_cache: dict[str, dict[str, str]] = {}


def available_languages() -> list[str]:
    langs = []
    if os.path.isdir(LANG_DIR):
        for name in sorted(os.listdir(LANG_DIR)):
            if name.startswith("lang_") and name.endswith(".json"):
                langs.append(name[5:-5])
    return langs or [DEFAULT_LANG, FALLBACK_LANG]


def _load(lang: str) -> dict[str, str]:
    if lang not in _cache:
        path = os.path.join(LANG_DIR, f"lang_{lang}.json")
        try:
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except FileNotFoundError:
            _cache[lang] = {}
    return _cache[lang]


def translate(lang: str, key: str) -> str:
    for candidate in (lang, DEFAULT_LANG, FALLBACK_LANG):
        text = _load(candidate).get(key)
        if text:
            return text
    return key
