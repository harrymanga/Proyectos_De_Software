"""Diálogo de exportación de mod a ZIP con un clic.

Basado en Langbergio/Factorio-Mod-Creator-Studio (export ZIP)
y justarandomgeek/factoriomod-debug (packaging and publishing).

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.factorio_mod import FactorioMod
from src.core.i18n import translate
from src.core.logger import get_logger

logger = get_logger(__name__)


class ExportModDialog(QWidget):
    """Diálogo para exportar un mod de Factorio a archivo ZIP."""

    def __init__(
        self,
        mod: FactorioMod | None = None,
        mod_dir: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.mod = mod
        self.mod_dir = Path(mod_dir) if mod_dir else None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Seleccionar carpeta de destino...")
        btn_output = QPushButton("Examinar...")
        btn_output.clicked.connect(self._select_output)
        output_row = QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.setSpacing(5)
        output_row.addWidget(self.output_edit)
        output_row.addWidget(btn_output)
        form.addRow(translate("dialog.create_mod.save_as"), output_row)

        self.zip_name_edit = QLineEdit()
        self.zip_name_edit.setPlaceholderText("ej. MiMod_1.0.0.zip")
        form.addRow("Nombre del archivo ZIP:", self.zip_name_edit)

        layout.addLayout(form)

        info_label = QLabel(
            "El archivo ZIP generado será compatible con Factorio "
            "y podrá instalarse directamente en la carpeta mods/."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.export_btn = QPushButton(translate("dialog.create_mod.create"))
        self.export_btn.clicked.connect(self._export_mod)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _select_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino"
        )
        if folder:
            self.output_edit.setText(folder)

    def _export_mod(self) -> None:
        output_text = self.output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(
                self,
                translate("factorio.export_zip"),
                "Debe seleccionar una carpeta de destino.",
            )
            return

        output_dir = Path(output_text)
        if not output_dir.exists() or not output_dir.is_dir():
            QMessageBox.warning(
                self,
                translate("factorio.export_zip"),
                "La carpeta de destino no es válida.",
            )
            return

        zip_name = self.zip_name_edit.text().strip()
        if not zip_name:
            if self.mod:
                zip_name = f"{self.mod.metadata.name}_{self.mod.metadata.version}.zip"
            else:
                QMessageBox.warning(
                    self,
                    translate("factorio.export_zip"),
                    "Debe especificar un nombre para el archivo ZIP.",
                )
                return

        try:
            if self.mod_dir:
                # Exportar desde directorio existente
                from src.core.factorio_export import FactorioExporter
                from src.core.factorio_mod import ModMetadata

                meta = self.mod.metadata if self.mod else ModMetadata(
                    name=zip_name.replace(".zip", ""),
                    version="1.0.0",
                )
                exporter = FactorioExporter(meta)
                exporter.export_from_directory(self.mod_dir, output_dir / zip_name)
            elif self.mod:
                # Exportar desde objeto mod
                exporter = FactorioExporter(self.mod)
                exporter.export_zip(output_dir / zip_name)
            else:
                QMessageBox.warning(
                    self,
                    translate("factorio.export_zip"),
                    "No hay mod para exportar.",
                )
                return

            QMessageBox.information(
                self,
                translate("factorio.export_zip"),
                f"Mod exportado exitosamente a:\n{output_dir / zip_name}",
            )

        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error exportando mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("factorio.export_zip"),
                f"Error exportando mod: {exc}",
            )
