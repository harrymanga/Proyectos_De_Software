"""Cobertura i18n: 6 idiomas, 43 claves, sin _metadata como clave."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ["es", "en", "fr", "de", "pt", "ar"]
EXPECTED = 43


def _load(lang):
    d = json.loads((ROOT / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if k != "_metadata"}


def test_all_locales_present():
    for lang in LOCALES:
        assert (ROOT / "translations" / f"{lang}.json").exists(), f"falta {lang}.json"


def test_key_count():
    for lang in LOCALES:
        assert len(_load(lang)) == EXPECTED, f"{lang} tiene {len(_load(lang))} claves"


def test_key_sets_match():
    ref = set(_load("es").keys())
    for lang in LOCALES[1:]:
        assert set(_load(lang).keys()) == ref, f"{lang} difiere de es"


def test_no_empty_values():
    for lang in LOCALES:
        for k, v in _load(lang).items():
            assert isinstance(v, str) and v.strip(), f"{lang}:{k} vacío"


def test_language_manager_supports_ar():
    from core.language_manager import LanguageManager
    assert "ar" in LanguageManager.SUPPORTED_LANGUAGES
    assert LanguageManager.SUPPORTED_LANGUAGES["ar"]["rtl"] is True
