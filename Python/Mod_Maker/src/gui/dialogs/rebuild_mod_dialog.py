"""Diálogo para reconstruir un mod de Factorio desde carpeta extraída."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
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


class RebuildModDialog(QWidget):
    """Diálogo para reconstruir (reempaquetar) un mod extraído de Factorio.

    Diseñado para ser embebido como pestaña en la ventana principal.
    """

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self._source_dir: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)
        btn_source = QPushButton(translate("dialog.rebuild_mod.select_folder"))
        btn_source.clicked.connect(self._select_source)
        source_row = QHBoxLayout()
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.setSpacing(5)
        source_row.addWidget(self.source_edit)
        source_row.addWidget(btn_source)
        form.addRow(translate("dialog.rebuild_mod.select_folder"), source_row)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        btn_output = QPushButton(translate("dialog.create_mod.save_as"))
        btn_output.clicked.connect(self._select_output)
        output_row = QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.setSpacing(5)
        output_row.addWidget(self.output_edit)
        output_row.addWidget(btn_output)
        form.addRow(translate("dialog.create_mod.save_as"), output_row)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.build_btn = QPushButton(translate("dialog.create_mod.create"))
        self.build_btn.clicked.connect(self._build_mod)
        self.build_btn.setEnabled(False)
        btn_layout.addWidget(self.build_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _select_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            translate("dialog.rebuild_mod.select_folder"),
            str(Path.cwd()),
        )
        if folder:
            self.source_edit.setText(folder)
            self._source_dir = Path(folder)

    def _select_output(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            translate("dialog.create_mod.save_as"),
            str(Path.cwd()),
            "Archivos ZIP (*.zip)",
        )
        if file_path:
            self.output_edit.setText(file_path)

    def _build_mod(self) -> None:
        if not self._source_dir or not self._source_dir.is_dir():
            QMessageBox.warning(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.create_mod.error_name_invalid"),
            )
            return

        output_zip, _ = QFileDialog.getSaveFileName(
            self,
            translate("dialog.create_mod.save_as"),
            f"{self._source_dir.name}.zip",
            "Archivos ZIP (*.zip)",
        )
        if not output_zip:
            return

        output_path = Path(output_zip)
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        try:
            from src.core.mod_packager import build_mod_zip

            build_mod_zip(self._source_dir, output_path)
            QMessageBox.information(
                self,
                translate("dialog.rebuild_mod.title"),
                translate(
                    "dialog.create_mod.success",
                    name=self._source_dir.name,
                    version="1.0.0",
                    output=output_path,
                ),
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error reconstruyendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.create_mod.error_build", error=str(exc)),
            )
