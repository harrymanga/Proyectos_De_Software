"""Entry point de la GUI: `appimage-builder-gui`."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from appimage_builder.gui.styles.themes import apply_theme, saved_theme
from appimage_builder.gui.wizard.wizard import AppImageWizard


def main(argv: list[str] | None = None) -> int:
    """Crea la QApplication, muestra el wizard y devuelve el exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    initial: Path | None = None
    if args:
        candidate = Path(args[0]).expanduser()
        if candidate.exists():
            initial = candidate

    app = QApplication(args)
    app.setApplicationName("appimage-builder")
    app.setOrganizationName("appimage-builder")
    apply_theme(app, saved_theme())

    wizard = AppImageWizard(initial_path=initial)
    wizard.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
