"""Temas QSS claro/oscuro con persistencia en QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

LIGHT_QSS = """
QWizard { background: palette(window); }
QTextEdit { background: palette(base); }
QProgressBar { border: 1px solid palette(mid); border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #2f7ed8; border-radius: 3px; }
QLabel[error="true"] { color: #c0392b; }
"""

DARK_QSS = """
QWidget { background-color: #2b2e33; color: #e6e6e6; }
QWizard { background: #2b2e33; }
QLineEdit, QTextEdit, QComboBox { background-color: #3a3e44; color: #e6e6e6;
    border: 1px solid #555b63; border-radius: 4px; padding: 3px; }
QPushButton { background-color: #3a3e44; border: 1px solid #555b63;
    border-radius: 4px; padding: 5px 12px; }
QPushButton:hover { background-color: #454b53; }
QPushButton:disabled { color: #888888; }
QProgressBar { border: 1px solid #555b63; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #2f7ed8; border-radius: 3px; }
QGroupBox { border: 1px solid #555b63; border-radius: 4px; margin-top: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; }
QLabel[error="true"] { color: #e74c3c; }
QToolTip { background-color: #454b53; color: #ffffff; border: 1px solid #666; }
"""

_THEMES = {"claro": LIGHT_QSS, "oscuro": DARK_QSS, "sistema": ""}
_SETTINGS_KEY = "theme"


def available_themes() -> list[str]:
    return ["sistema", "claro", "oscuro"]


def saved_theme() -> str:
    theme = QSettings("appimage-builder", "appimage-builder").value(_SETTINGS_KEY, "sistema")
    return theme if theme in _THEMES else "sistema"


def apply_theme(app: QApplication | None = None, name: str = "sistema") -> str:
    """Aplica el tema, lo persiste y devuelve el nombre efectivo."""
    if name not in _THEMES:
        name = "sistema"
    target = QApplication.instance() if app is None else app
    if target is not None:
        target.setStyleSheet(_THEMES[name])
    QSettings("appimage-builder", "appimage-builder").setValue(_SETTINGS_KEY, name)
    return name
