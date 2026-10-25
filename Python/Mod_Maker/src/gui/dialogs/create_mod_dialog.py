"""Diálogo para crear un mod nuevo de Factorio."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class CreateModDialog(QDialog):
    """Diálogo asistente para crear un mod nuevo de Factorio."""

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle(translate("dialog.create_mod.title"))
        self.setMinimumWidth(500)
        self._content_folder: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Metadatos del mod
        meta_group = QGroupBox(translate("dialog.create_mod.title"))
        meta_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(translate("dialog.create_mod.name"))
        meta_layout.addRow(translate("dialog.create_mod.name"), self.name_edit)

        self.version_edit = QLineEdit("1.0.0")
        meta_layout.addRow(translate("dialog.create_mod.version"), self.version_edit)

        self.author_edit = QLineEdit()
        meta_layout.addRow(translate("dialog.create_mod.author"), self.author_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        meta_layout.addRow(translate("dialog.create_mod.description"), self.description_edit)

        self.factorio_version_edit = QLineEdit("1.1")
        meta_layout.addRow(
            translate("dialog.create_mod.factorio_version"), self.factorio_version_edit
        )

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Carpeta de contenido
        content_group = QGroupBox("Contenido del mod")
        content_layout = QVBoxLayout()

        self.folder_label = QLabel(translate("dialog.create_mod.select_folder"))
        self.folder_label.setWordWrap(True)

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("Seleccionar carpeta...")
        self.select_btn.clicked.connect(self._select_folder)
        btn_layout.addWidget(self.select_btn)
        btn_layout.addStretch()

        content_layout.addWidget(self.folder_label)
        content_layout.addLayout(btn_layout)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # Botones
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._create_mod)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            translate("dialog.create_mod.create")
        )
        layout.addWidget(self.button_box)

    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, translate("dialog.create_mod.select_folder")
        )
        if folder:
            self._content_folder = Path(folder)
            self.folder_label.setText(
                translate("dialog.create_mod.folder_selected", folder=folder)
            )

    def _create_mod(self) -> None:
        name = self.name_edit.text().strip()
        version = self.version_edit.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_name"),
            )
            return

        if not self._content_folder or not self._content_folder.is_dir():
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.select_folder"),
            )
            return

        output_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar mod como",
            f"{name}.zip",
            "Archivos ZIP (*.zip)",
        )
        if not output_zip:
            return

        output_path = Path(output_zip)
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        try:
            metadata = self.plugin.create_info_json(
                name=name,
                version=version,
                author=self.author_edit.text().strip(),
                description=self.description_edit.toPlainText().strip(),
                factorio_version=self.factorio_version_edit.text().strip(),
            )

            temp_dir = self._content_folder / ".modmaker_build"
            temp_dir.mkdir(exist_ok=True)

            # Copiar contenido a carpeta temporal
            import shutil

            for item in self._content_folder.iterdir():
                if item.name == ".modmaker_build":
                    continue
                if item.is_file():
                    shutil.copy2(item, temp_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, temp_dir / item.name, dirs_exist_ok=True)

            self.plugin.save_info_json(temp_dir, metadata)
            self.plugin.build(temp_dir, output_path)

            # Limpiar carpeta temporal
            shutil.rmtree(temp_dir, ignore_errors=True)

            QMessageBox.information(
                self,
                translate("dialog.create_mod.title"),
                translate(
                    "dialog.create_mod.success",
                    name=name,
                    version=version,
                    output=output_path,
                ),
            )
            self.accept()

        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error creando mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_build", error=str(exc)),
            )
