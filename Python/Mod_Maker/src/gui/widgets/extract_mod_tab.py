"""Pestaña integrada para extraer mods de Factorio.

Sustituye al diálogo modal ExtractModDialog. Se abre como pestaña dentro
de la ventana principal, al estilo de un IDE (VS Code).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class ExtractModTab(QWidget):
    """Pestaña para extraer el contenido de un mod de Factorio."""

    mod_extracted = Signal(str)

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self._mod_path: Path | None = None
        self.setWindowTitle(translate("dialog.extract_mod.title"))
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Seleccione un mod .zip para extraer su contenido a una carpeta de trabajo."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.mod_edit = QLineEdit()
        self.mod_edit.setReadOnly(True)
        btn_mod = QPushButton("Seleccionar mod...")
        btn_mod.clicked.connect(self._select_mod)
        mod_row = QHBoxLayout()
        mod_row.addWidget(self.mod_edit)
        mod_row.addWidget(btn_mod)
        layout.addLayout(mod_row)

        self.dest_edit = QLineEdit()
        self.dest_edit.setReadOnly(True)
        btn_dest = QPushButton("Seleccionar destino...")
        btn_dest.clicked.connect(self._select_destination)
        dest_row = QHBoxLayout()
        dest_row.addWidget(self.dest_edit)
        dest_row.addWidget(btn_dest)
        layout.addLayout(dest_row)

        btn_action = QPushButton(translate("dialog.extract_mod.extract"))
        btn_action.clicked.connect(self._extract)
        layout.addWidget(btn_action)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _select_mod(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            translate("dialog.extract_mod.select_mod"),
            "",
            "Archivos ZIP (*.zip)",
        )
        if file_path:
            self._mod_path = Path(file_path)
            self.mod_edit.setText(str(file_path))

    def _select_destination(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, translate("dialog.extract_mod.destination")
        )
        if folder:
            self.dest_edit.setText(folder)

    def _extract(self) -> None:
        if not self._mod_path:
            QMessageBox.warning(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.select_mod"),
            )
            return

        dest_text = self.dest_edit.text().strip()
        if not dest_text:
            QMessageBox.warning(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.destination"),
            )
            return

        dest_dir = Path(dest_text)

        try:
            self.plugin.extract(self._mod_path, dest_dir)
            self.status_label.setText(
                translate("dialog.extract_mod.success", dest=dest_dir)
            )
            self.mod_extracted.emit(str(dest_dir))
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error extrayendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.error", error=str(exc)),
            )
