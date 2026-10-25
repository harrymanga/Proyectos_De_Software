"""Pruebas unitarias para I18nManager."""

from __future__ import annotations

from src.core.i18n import I18nManager, translate


def test_available_languages_include_es_and_en() -> None:
    """Español e inglés deben estar disponibles por defecto."""
    langs = I18nManager().get_available_languages()
    assert "es" in langs
    assert "en" in langs


def test_translate_returns_spanish_by_default() -> None:
    """El idioma por defecto es español."""
    i18n = I18nManager(language="es")
    assert i18n.translate("app.title") == "Mod Maker"


def test_translate_returns_english() -> None:
    """Se puede cambiar a inglés."""
    i18n = I18nManager(language="en")
    assert i18n.translate("app.title") == "Mod Maker"


def test_translate_missing_key_returns_key() -> None:
    """Una clave inexistente devuelve la propia clave."""
    i18n = I18nManager(language="es")
    assert i18n.translate("clave.inexistente") == "clave.inexistente"


def test_translate_with_kwargs() -> None:
    """Las claves con placeholders se formatean con kwargs."""
    i18n = I18nManager(language="en")
    assert i18n.translate("app.version", version="0.1.0") == "Version 0.1.0"


def test_global_translate_function() -> None:
    """La función global translate funciona."""
    assert translate("app.title") == "Mod Maker"


def test_validate_keys_no_missing() -> None:
    """No debe haber claves faltantes entre español e inglés."""
    i18n = I18nManager()
    missing = i18n.validate_keys()
    # Todas las claves de español deben estar en inglés y viceversa
    assert missing == []
