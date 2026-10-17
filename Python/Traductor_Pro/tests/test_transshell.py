"""Pruebas del motor trans-shell (con subprocess simulado, sin red)."""
import subprocess

import pytest

from traductor_pro.domain.entities import TranslationEngine, TranslationRequest
from traductor_pro.infrastructure.translators.translator_factory import TranslatorFactory
from traductor_pro.infrastructure.translators.transshell_translator import (
    TransShellTranslatorAdapter,
)


class FakeKeyManager:
    def get(self, service):
        return None


def _request(text="Hello world"):
    return TranslationRequest(source_text=text, target_lang="es", engine=TranslationEngine.TRANSSHELL)


class _Completed:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class TestTransShellTranslator:
    def test_translate_ok(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/trans")
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **k: _Completed(stdout="Hola mundo\n"),
        )
        result = TransShellTranslatorAdapter().translate(_request())
        assert result.success is True
        assert result.translated_text == "Hola mundo"

    def test_missing_binary_raises(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        with pytest.raises(RuntimeError):
            TransShellTranslatorAdapter().translate(_request())

    def test_echo_is_failure(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/trans")
        monkeypatch.setattr(
            subprocess, "run",
            lambda *a, **k: _Completed(stdout="Hello world\n"),
        )
        result = TransShellTranslatorAdapter().translate(_request())
        assert result.success is False
        assert "idéntico" in (result.error or "")

    def test_engine_flag(self, monkeypatch):
        seen = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"] = cmd
            return _Completed(stdout="Hola\n")

        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/trans")
        monkeypatch.setattr(subprocess, "run", fake_run)
        TransShellTranslatorAdapter(engine="bing").translate(_request())
        assert "-e" in seen["cmd"] and "bing" in seen["cmd"]

    def test_factory_registers_engine(self):
        translators = TranslatorFactory.create_all(FakeKeyManager())
        assert TranslationEngine.TRANSSHELL in translators
        assert isinstance(
            TranslatorFactory.create(TranslationEngine.TRANSSHELL, FakeKeyManager()),
            TransShellTranslatorAdapter,
        )
