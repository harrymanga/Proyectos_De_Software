"""Pestaña integrada para reconstruir mods de Factorio.

Sustituye al diálogo modal RebuildModDialog. Se abre como pestaña dentro
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


class RebuildModTab(QWidget):
    """Pestaña para reconstruir (reempaquetar) un mod extraído de Factorio."""

    mod_rebuilt = Signal(str)

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self._source_dir: Path | None = None
        self.setWindowTitle(translate("dialog.rebuild_mod.title"))
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Seleccione la carpeta con el mod extraído para reconstruirlo como archivo .zip."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)
        btn_source = QPushButton("Seleccionar carpeta...")
        btn_source.clicked.connect(self._select_source)
        source_row = QHBoxLayout()
        source_row.addWidget(self.source_edit)
        source_row.addWidget(btn_source)
        layout.addLayout(source_row)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        btn_output = QPushButton("Seleccionar archivo de salida...")
        btn_output.clicked.connect(self._select_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(btn_output)
        layout.addLayout(output_row)

        btn_action = QPushButton(translate("dialog.rebuild_mod.build"))
        btn_action.clicked.connect(self._rebuild)
        layout.addWidget(btn_action)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

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
            self.status_label.setText(
                translate("dialog.rebuild_mod.success", output=output_path)
            )
            self.mod_rebuilt.emit(str(output_path))
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error reconstruyendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.rebuild_mod.title"),
                translate("dialog.rebuild_mod.error", error=str(exc)),
            )
