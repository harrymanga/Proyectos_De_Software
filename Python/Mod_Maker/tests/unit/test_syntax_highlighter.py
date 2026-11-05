"""Pruebas unitarias para SyntaxHighlighter."""

from __future__ import annotations

from PySide6.QtGui import QTextDocument

from src.core.syntax_highlighter import (
    CfgHighlighter,
    JsonHighlighter,
    LuaHighlighter,
    PlainTextHighlighter,
    SyntaxHighlighterFactory,
    TomlHighlighter,
)


def test_lua_highlighter() -> None:
    """Verifica que el highlighter de Lua se crea correctamente."""
    doc = QTextDocument()
    highlighter = LuaHighlighter(doc)
    assert highlighter is not None


def test_json_highlighter() -> None:
    """Verifica que el highlighter de JSON se crea correctamente."""
    doc = QTextDocument()
    highlighter = JsonHighlighter(doc)
    assert highlighter is not None


def test_toml_highlighter() -> None:
    """Verifica que el highlighter de TOML se crea correctamente."""
    doc = QTextDocument()
    highlighter = TomlHighlighter(doc)
    assert highlighter is not None


def test_cfg_highlighter() -> None:
    """Verifica que el highlighter de CFG se crea correctamente."""
    doc = QTextDocument()
    highlighter = CfgHighlighter(doc)
    assert highlighter is not None


def test_plain_text_highlighter() -> None:
    """Verifica que el highlighter de texto plano se crea correctamente."""
    doc = QTextDocument()
    highlighter = PlainTextHighlighter(doc)
    assert highlighter is not None


def test_syntax_highlighter_factory_lua() -> None:
    """Verifica que la fábrica crea el highlighter correcto para archivos .lua."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "test.lua")
    assert isinstance(highlighter, LuaHighlighter)


def test_syntax_highlighter_factory_json() -> None:
    """Verifica que la fábrica crea el highlighter correcto para archivos .json."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "info.json")
    assert isinstance(highlighter, JsonHighlighter)


def test_syntax_highlighter_factory_cfg() -> None:
    """Verifica que la fábrica crea el highlighter correcto para archivos .cfg."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "settings.cfg")
    assert isinstance(highlighter, CfgHighlighter)


def test_syntax_highlighter_factory_toml() -> None:
    """Verifica que la fábrica crea el highlighter correcto para archivos .toml."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "config.toml")
    assert isinstance(highlighter, TomlHighlighter)


def test_syntax_highlighter_factory_txt() -> None:
    """Verifica que la fábrica crea el highlighter correcto para archivos .txt."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "readme.txt")
    assert isinstance(highlighter, PlainTextHighlighter)


def test_syntax_highlighter_factory_unknown() -> None:
    """Verifica que la fábrica devuelve un highlighter base para extensiones desconocidas."""
    doc = QTextDocument()
    highlighter = SyntaxHighlighterFactory.create(doc, "file.xyz")
    assert highlighter is not None
    from PySide6.QtGui import QSyntaxHighlighter
    assert isinstance(highlighter, QSyntaxHighlighter)
