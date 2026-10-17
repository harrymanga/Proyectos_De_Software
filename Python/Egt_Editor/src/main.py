"""Punto de entrada documentado (§55)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from i18n import I18n


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("EGT-Tools")
    app.setApplicationName("EGT Editor Exciter3")
    i18n = I18n(default="es")
    win = MainWindow(i18n)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
