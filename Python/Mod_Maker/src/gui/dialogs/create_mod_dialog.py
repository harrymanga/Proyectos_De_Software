"""Diálogo para crear un mod nuevo de Factorio basado en la documentación oficial.

Referencias:
- https://wiki.factorio.com/Modding
- https://wiki.factorio.com/Tutorial:Modding_tutorial/Gangsir
- https://lua-api.factorio.com/latest/auxiliary/mod-structure.html

Estructura de un mod válido:
    <mod-name>/
        info.json          (obligatorio)
        data.lua           (opcional - prototipos)
        data-updates.lua   (opcional)
        data-final-fixes.lua (opcional)
        control.lua        (opcional - scripting en tiempo de ejecución)
        settings.lua       (opcional - configuración)
        locale/
            en/
                any_name.cfg
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
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
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)

# Versiones de Factorio soportadas
FACTORIO_VERSIONS = ["2.0", "2.1"]

# Expresión regular para nombres válidos de mods de Factorio:
# Solo letras minúsculas, números y guiones. No puede empezar ni terminar con guion.
MOD_NAME_REGEX = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"


class CreateModDialog(QWidget):
    """Diálogo asistente para crear un mod nuevo de Factorio.

    Sigue las directrices de la documentación oficial de Factorio para
    crear mods válidos con la estructura correcta de carpetas y archivos.

    Diseñado para ser embebido como pestaña en la ventana principal.
    """

    mod_created = Signal(str)

    def __init__(self, plugin: FactorioPlugin, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self._content_folder: Path | None = None
        self._setup_ui()
        self._setup_validators()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ==================================================================
        # Metadatos del mod (info.json)
        # ==================================================================
        meta_group = QGroupBox(translate("dialog.create_mod.metadata_group"))
        meta_layout = QFormLayout()
        meta_layout.setContentsMargins(5, 5, 5, 5)
        meta_layout.setSpacing(5)

        # Nombre del mod (obligatorio, solo minúsculas, números y guiones)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            translate("dialog.create_mod.name_placeholder")
        )
        self.name_edit.textChanged.connect(self._validate_name)
        self.name_label = QLabel(translate("dialog.create_mod.name"))
        self.name_label.setToolTip(
            translate("dialog.create_mod.name_tooltip")
        )
        meta_layout.addRow(self.name_label, self.name_edit)
        self.name_hint_label = QLabel("")
        self.name_hint_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
        meta_layout.addRow("", self.name_hint_label)

        # Título (opcional pero recomendado)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(
            translate("dialog.create_mod.title_placeholder")
        )
        meta_layout.addRow(translate("dialog.create_mod.title"), self.title_edit)

        # Autor (opcional)
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText(
            translate("dialog.create_mod.author_placeholder")
        )
        meta_layout.addRow(translate("dialog.create_mod.author"), self.author_edit)

        # Descripción (opcional)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText(
            translate("dialog.create_mod.description_placeholder")
        )
        meta_layout.addRow(translate("dialog.create_mod.description"), self.description_edit)

        # Versión del mod (obligatorio, formato X.Y.Z)
        self.version_edit = QLineEdit("1.0.0")
        self.version_edit.setPlaceholderText("1.0.0")
        meta_layout.addRow(translate("dialog.create_mod.version"), self.version_edit)

        # Versión de Factorio (obligatorio)
        self.factorio_version_edit = QLineEdit("2.0")
        meta_layout.addRow(
            translate("dialog.create_mod.factorio_version"),
            self.factorio_version_edit,
        )

        # Página web (opcional)
        self.homepage_edit = QLineEdit()
        self.homepage_edit.setPlaceholderText(
            translate("dialog.create_mod.homepage_placeholder")
        )
        meta_layout.addRow(translate("dialog.create_mod.homepage"), self.homepage_edit)

        # Dependencias (opcional)
        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setPlaceholderText(
            translate("dialog.create_mod.dependencies_placeholder")
        )
        meta_layout.addRow(translate("dialog.create_mod.dependencies"), self.dependencies_edit)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # ==================================================================
        # Carpeta de contenido
        # ==================================================================
        content_group = QGroupBox(translate("dialog.create_mod.content_group"))
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)

        self.folder_label = QLabel(translate("dialog.create_mod.no_folder"))
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet("color: #ffaa00;")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)
        self.select_btn = QPushButton(translate("dialog.create_mod.select_folder"))
        self.select_btn.clicked.connect(self._select_folder)
        btn_layout.addWidget(self.select_btn)
        btn_layout.addStretch()

        content_layout.addWidget(self.folder_label)
        content_layout.addLayout(btn_layout)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # ==================================================================
        # Información sobre estructura
        # ==================================================================
        info_group = QGroupBox(translate("dialog.create_mod.structure_group"))
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)
        info_text = QLabel(
            translate("dialog.create_mod.structure_info")
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ==================================================================
        # Botones
        # ==================================================================
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.create_btn = QPushButton(translate("dialog.create_mod.create"))
        self.create_btn.clicked.connect(self._create_mod)
        self.create_btn.setEnabled(False)
        btn_layout.addWidget(self.create_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _setup_validators(self) -> None:
        """Configura validadores para los campos de entrada."""
        # Validador para nombre de mod: solo minúsculas, números y guiones
        name_regex = QRegularExpression(MOD_NAME_REGEX)
        name_validator = QRegularExpressionValidator(name_regex, self)
        self.name_edit.setValidator(name_validator)

        # Validador para versión: número.número.número
        version_regex = QRegularExpression(r"^\d+\.\d+\.\d+$")
        version_validator = QRegularExpressionValidator(version_regex, self)
        self.version_edit.setValidator(version_validator)

    def _validate_name(self) -> None:
        """Valida el nombre del mod en tiempo real."""
        name = self.name_edit.text().strip()
        if not name:
            self.name_hint_label.setText("")
            self.name_hint_label.setStyleSheet("")
            self._update_create_button()
            return

        if re.match(MOD_NAME_REGEX, name):
            self.name_hint_label.setText(
                translate("dialog.create_mod.name_valid")
            )
            self.name_hint_label.setStyleSheet("color: #00aa00; font-size: 11px;")
        else:
            self.name_hint_label.setText(
                translate("dialog.create_mod.name_invalid")
            )
            self.name_hint_label.setStyleSheet("color: #ff6666; font-size: 11px;")

        self._update_create_button()

    def _validate_version(self) -> None:
        """Valida el formato de la versión."""
        version = self.version_edit.text().strip()
        if not version:
            return False
        import re
        return bool(re.match(r"^\d+\.\d+\.\d+$", version))

    def _update_create_button(self) -> None:
        """Habilita/deshabilita el botón Crear según la validez del formulario."""
        name = self.name_edit.text().strip()
        name_valid = bool(name and re.match(MOD_NAME_REGEX, name))
        version_valid = self._validate_version()
        folder_valid = self._content_folder is not None and self._content_folder.is_dir()

        self.create_btn.setEnabled(name_valid and version_valid and folder_valid)

    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            translate("dialog.create_mod.select_folder"),
        )
        if folder:
            self._content_folder = Path(folder)
            self.folder_label.setText(
                translate("dialog.create_mod.folder_selected", folder=folder)
            )
            self.folder_label.setStyleSheet("color: #00aa00;")
            self._update_create_button()

    def _create_mod(self) -> None:
        """Crea el mod validando todos los campos según la documentación de Factorio."""
        name = self.name_edit.text().strip()
        version = self.version_edit.text().strip()

        # Validar nombre
        if not name:
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_name_required"),
            )
            return

        if not re.match(MOD_NAME_REGEX, name):
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_name_invalid"),
            )
            return

        # Validar versión
        if not version or not self._validate_version():
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_version_invalid"),
            )
            return

        # Validar carpeta de contenido
        if not self._content_folder or not self._content_folder.is_dir():
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.select_folder"),
            )
            return

        output_zip, _ = QFileDialog.getSaveFileName(
            self,
            translate("dialog.create_mod.save_as"),
            f"{name}_{version}.zip",
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
                dependencies=[
                    d.strip() for d in self.dependencies_edit.text().split(",")
                    if d.strip()
                ],
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

        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error creando mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_build", error=str(exc)),
            )
