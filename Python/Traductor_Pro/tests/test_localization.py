"""Pruebas de internacionalización (es/en) y temas."""
import os

import pytest

from traductor_pro.infrastructure.localization.manager import LanguageManager
from traductor_pro.infrastructure.ui.themes import DARK_QSS, apply_theme


class TestLanguageManager:
    def test_available_languages(self):
        manager = LanguageManager()
        assert "es" in manager.available()
        assert "en" in manager.available()

    def test_default_is_spanish(self):
        manager = LanguageManager()
        assert manager.current == "es"
        assert manager.tr("btn.translate") == "Traducir"

    def test_switch_to_english(self):
        manager = LanguageManager()
        assert manager.set_language("en") is True
        assert manager.current == "en"
        assert manager.tr("btn.translate") == "Translate"

    def test_invalid_language_rejected(self):
        manager = LanguageManager()
        assert manager.set_language("xx") is False
        assert manager.current == "es"

    def test_unknown_key_returns_key(self):
        manager = LanguageManager()
        assert manager.tr("no.existe") == "no.existe"

    def test_format_params(self):
        manager = LanguageManager()
        assert manager.tr("msg.files_done", total=3) == "Archivos procesados: 3"
        manager.set_language("en")
        assert manager.tr("msg.files_done", total=3) == "Processed files: 3"

    def test_language_names(self):
        manager = LanguageManager()
        assert manager.language_name("es") == "Español"
        assert manager.language_name("en") == "English"

    def test_catalogs_share_keys(self):
        manager = LanguageManager()
        es_keys = set(manager._catalogs["es"])
        en_keys = set(manager._catalogs["en"])
        assert es_keys == en_keys


class FakeApp:
    def __init__(self):
        self.stylesheet = None

    def setStyleSheet(self, value):
        self.stylesheet = value


class TestThemes:
    def test_dark_applies_qss(self):
        app = FakeApp()
        apply_theme(app, True)
        assert app.stylesheet == DARK_QSS
        assert "QPushButton" in app.stylesheet

    def test_light_clears_qss(self):
        app = FakeApp()
        apply_theme(app, True)
        apply_theme(app, False)
        assert app.stylesheet == ""
