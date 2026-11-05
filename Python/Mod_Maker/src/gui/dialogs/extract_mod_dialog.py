"""Diálogo para extraer el contenido de un mod de Factorio."""

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


class ExtractModDialog(QWidget):
    """Diálogo para extraer el contenido de un mod de Factorio.

    Diseñado para ser embebido como pestaña en la ventana principal.
    """

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self._mod_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.mod_edit = QLineEdit()
        self.mod_edit.setReadOnly(True)
        btn_mod = QPushButton(translate("dialog.extract_mod.select_mod"))
        btn_mod.clicked.connect(self._select_mod)
        mod_row = QHBoxLayout()
        mod_row.setContentsMargins(0, 0, 0, 0)
        mod_row.setSpacing(5)
        mod_row.addWidget(self.mod_edit)
        mod_row.addWidget(btn_mod)
        form.addRow(translate("dialog.extract_mod.select_mod"), mod_row)

        layout.addLayout(form)

        self.mod_edit.textChanged.connect(self._on_mod_changed)

    def _on_mod_changed(self) -> None:
        self._mod_path = Path(self.mod_edit.text()) if self.mod_edit.text() else None

    def _select_mod(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            translate("dialog.extract_mod.select_mod_file"),
            str(Path.cwd()),
            "Mods de Factorio (*.zip)",
        )
        if file_path:
            self.mod_edit.setText(file_path)
            self._mod_path = Path(file_path)

    def _extract_mod(self) -> None:
        """Extrae el mod seleccionado."""
        if not self._mod_path or not self._mod_path.exists():
            QMessageBox.warning(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.error_no_file"),
            )
            return

        output_dir, _ = QFileDialog.getExistingDirectory(
            self,
            translate("dialog.extract_mod.select_output_folder"),
            str(Path.cwd()),
        )
        if not output_dir:
            return

        output_dir_path = Path(output_dir)
        try:
            self.plugin.extract(self._mod_path, output_dir_path)
            QMessageBox.information(
                self,
                translate("dialog.extract_mod.title"),
                translate(
                    "dialog.extract_mod.success",
                    output=output_dir_path,
                ),
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error extrayendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.extract_mod.title"),
                translate("dialog.extract_mod.error", error=str(exc)),
            )
