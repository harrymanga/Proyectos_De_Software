"""Diálogo para reconstruir un mod de Factorio desde carpeta extraída."""

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


class RebuildModDialog(QDialog):
    """Diálogo para reconstruir (reempaquetar) un mod extraído de Factorio."""

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle(translate("dialog.rebuild_mod.title"))
        self.setMinimumWidth(500)
        self._source_dir: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)
        btn_source = QPushButton("Seleccionar carpeta...")
        btn_source.clicked.connect(self._select_source)
        source_row = QHBoxLayout()
        source_row.addWidget(self.source_edit)
        source_row.addWidget(btn_source)
        form.addRow(translate("dialog.rebuild_mod.select_folder"), source_row)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        btn_output = QPushButton("Seleccionar archivo de salida...")
        btn_output.clicked.connect(self._select_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(btn_output)
        form.addRow(translate("dialog.rebuild_mod.output"), output_row)

        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._rebuild)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            translate("dialog.rebuild_mod.build")
        )
        layout.addWidget(self.button_box)

    def _select_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, translate("dialog.rebuild_mod.select_folder")
        )
        if folder:
            self._source_dir = Path(folder)
            self.source_edit.setText(folder)

    def _select_output(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar mod reconstruido como",
            "mod.zip",
            "Archivos ZIP (*.zip)",
        )
        if file_path:
            self.output_edit.setText(file_path)

    def _rebuild(self) -> None:
        if not self._source_dir or not self._source_dir.is_dir():
            QMessageBox.warning(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.rebuild_mod.select_folder"),
            )
            return

        output_text = self.output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.rebuild_mod.output"),
            )
            return

        output_path = Path(output_text)
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        try:
            self.plugin.build(self._source_dir, output_path)
            QMessageBox.information(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.rebuild_mod.success", output=output_path),
            )
            self.accept()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error reconstruyendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.rebuild_mod.error", error=str(exc)),
            )
