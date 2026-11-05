"""Syntax Highlighter para diferentes lenguajes de mod de Factorio.

Soporta:
- Lua (.lua)
- JSON (.json)
- TOML (.toml)
- CFG (.cfg)
- Texto plano (.txt, .md, .csv)
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    """Crea un formato de texto con el color y estilo dados."""
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt


class LuaHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para Lua."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.keyword_fmt = _fmt("#569CD6", bold=True)  # azul
        self.string_fmt = _fmt("#CE9178")  # naranja
        self.comment_fmt = _fmt("#6A9955", italic=True)  # verde
        self.function_fmt = _fmt("#DCDCAA")  # amarillo
        self.number_fmt = _fmt("#B5CEA8")  # gris claro

        self.keywords = [
            "and", "break", "do", "else", "elseif", "end", "false", "for",
            "function", "goto", "if", "in", "local", "nil", "not", "or",
            "repeat", "return", "then", "true", "until", "while",
        ]

        self.functions = [
            "print", "pairs", "ipairs", "type", "tostring", "tonumber",
            "require", "assert", "error", "select", "setmetatable",
            "getmetatable", "rawset", "rawget", "next", "pcall", "xpcall",
        ]

    def highlightBlock(self, text: str) -> None:
        # Palabras clave
        for word in self.keywords:
            pattern = QRegularExpression(rf"\b{word}\b")
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.keyword_fmt)

        # Funciones
        for func in self.functions:
            pattern = QRegularExpression(rf"\b{func}\b")
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.function_fmt)

        # Strings
        string_pattern = QRegularExpression(r'"[^"]*"|\'[^\']*\'')
        iterator = string_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_fmt)

        # Comentarios
        comment_pattern = QRegularExpression(r"--[^\n]*")
        iterator = comment_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.comment_fmt)

        # Números
        number_pattern = QRegularExpression(r"\b\d+\.?\d*\b")
        iterator = number_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.number_fmt)


class JsonHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para JSON."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.key_fmt = _fmt("#9CDCFE")  # azul claro
        self.string_fmt = _fmt("#CE9178")  # naranja
        self.number_fmt = _fmt("#B5CEA8")  # gris claro
        self.boolean_fmt = _fmt("#569CD6")  # azul
        self.null_fmt = _fmt("#6A9955")  # verde
        self.punctuation_fmt = _fmt("#D4D4D4")  # gris

    def highlightBlock(self, text: str) -> None:
        # Claves de JSON
        key_pattern = QRegularExpression(r'"[^"]*"(?=\s*:)')
        iterator = key_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.key_fmt)

        # Strings
        string_pattern = QRegularExpression(r'"[^"]*"')
        iterator = string_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_fmt)

        # Números
        number_pattern = QRegularExpression(r"\b\d+\.?\d*\b")
        iterator = number_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.number_fmt)

        # Booleanos y null
        bool_pattern = QRegularExpression(r"\b(true|false|null)\b")
        iterator = bool_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.boolean_fmt)

        # Puntuación
        punct_pattern = QRegularExpression(r"[{}\[\]:,]")
        iterator = punct_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.punctuation_fmt)


class TomlHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para TOML."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.header_fmt = _fmt("#C586C0", bold=True)  # púrpura
        self.key_fmt = _fmt("#9CDCFE")  # azul claro
        self.string_fmt = _fmt("#CE9178")  # naranja
        self.number_fmt = _fmt("#B5CEA8")  # gris claro
        self.boolean_fmt = _fmt("#569CD6")  # azul
        self.comment_fmt = _fmt("#6A9955", italic=True)  # verde

    def highlightBlock(self, text: str) -> None:
        # Headers de sección [section]
        header_pattern = QRegularExpression(r"\[[^\]]*\]")
        iterator = header_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.header_fmt)

        # Claves
        key_pattern = QRegularExpression(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=")
        iterator = key_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            key_end = match.capturedLength() - 1  # excluir el =
            self.setFormat(match.capturedStart(), key_end, self.key_fmt)

        # Strings
        string_pattern = QRegularExpression(r'"[^"]*"|\'[^\']*\'')
        iterator = string_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_fmt)

        # Comentarios
        comment_pattern = QRegularExpression(r"#.*")
        iterator = comment_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.comment_fmt)


class CfgHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para archivos CFG."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.key_fmt = _fmt("#9CDCFE")  # azul claro
        self.string_fmt = _fmt("#CE9178")  # naranja
        self.number_fmt = _fmt("#B5CEA8")  # gris claro
        self.boolean_fmt = _fmt("#569CD6")  # azul
        self.comment_fmt = _fmt("#6A9955", italic=True)  # verde

    def highlightBlock(self, text: str) -> None:
        # Claves key=value
        key_pattern = QRegularExpression(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=")
        iterator = key_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            key_end = match.capturedLength() - 1
            self.setFormat(match.capturedStart(), key_end, self.key_fmt)

        # Strings
        string_pattern = QRegularExpression(r'"[^"]*"|\'[^\']*\'')
        iterator = string_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.string_fmt)

        # Comentarios
        comment_pattern = QRegularExpression(r"#.*|;.*")
        iterator = comment_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.comment_fmt)


class PlainTextHighlighter(QSyntaxHighlighter):
    """Resaltador básico para texto plano."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.comment_fmt = _fmt("#6A9955", italic=True)

    def highlightBlock(self, text: str) -> None:
        comment_pattern = QRegularExpression(r"#.*|;.*|//.*")
        iterator = comment_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.comment_fmt)


class SyntaxHighlighterFactory:
    """Fábrica para crear el highlighter adecuado según la extensión del archivo."""

    @staticmethod
    def create(parent: QSyntaxHighlighter, file_path: str) -> QSyntaxHighlighter:
        ext = Path(file_path).suffix.lower()

        if ext == ".lua":
            return LuaHighlighter(parent)
        elif ext == ".json":
            return JsonHighlighter(parent)
        elif ext in (".toml",):
            return TomlHighlighter(parent)
        elif ext in (".cfg", ".ini", ".conf"):
            return CfgHighlighter(parent)
        elif ext in (".txt", ".md", ".csv", ".log"):
            return PlainTextHighlighter(parent)
        else:
            # Devolver un highlighter de texto plano por defecto
            return PlainTextHighlighter(parent)
