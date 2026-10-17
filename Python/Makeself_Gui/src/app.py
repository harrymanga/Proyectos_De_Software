"""Punto de entrada. Uso: python src/app.py [--lang es|en] [--theme light|dark]."""
from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from gui.main_window import MainWindow  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default=None)
    parser.add_argument("--theme", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = QApplication([])
    app.setOrganizationName("MakeselfGUI")
    app.setApplicationName("makeself-gui")
    settings = QSettings()
    lang = args.lang or settings.value("lang", "es")
    theme = args.theme or settings.value("theme", "light")
    settings.setValue("lang", lang)
    settings.setValue("theme", theme)
    theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes", f"{theme}.qss")
    if os.path.isfile(theme_path):
        with open(theme_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    window = MainWindow(lang=lang, theme=theme)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
