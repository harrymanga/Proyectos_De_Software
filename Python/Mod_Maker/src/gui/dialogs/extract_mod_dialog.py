"""Diálogo para extraer un mod de Factorio."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class ExtractModDialog(QDialog):
    """Diálogo para extraer el contenido de un mod de Factorio."""

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle(translate("dialog.extract_mod.title"))
        self.setMinimumWidth(500)
        self._mod_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.mod_edit = QLineEdit()
        self.mod_edit.setReadOnly(True)
        btn_mod = QPushButton("Seleccionar mod...")
        btn_mod.clicked.connect(self._select_mod)
        mod_row = QHBoxLayout()
        mod_row.addWidget(self.mod_edit)
        mod_row.addWidget(btn_mod)
        form.addRow(translate("dialog.extract_mod.select_mod"), mod_row)

        self.dest_edit = QLineEdit()
        self.dest_edit.setReadOnly(True)
        btn_dest = QPushButton("Seleccionar destino...")
        btn_dest.clicked.connect(self._select_destination)
        dest_row = QHBoxLayout()
        dest_row.addWidget(self.dest_edit)
        dest_row.addWidget(btn_dest)
        form.addRow(translate("dialog.extract_mod.destination"), dest_row)

        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._extract)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            translate("dialog.extract_mod.extract")
        )
        layout.addWidget(self.button_box)

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
            QMessageBox.information(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.success", dest=dest_dir),
            )
            self.accept()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error extrayendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.error", error=str(exc)),
            )
