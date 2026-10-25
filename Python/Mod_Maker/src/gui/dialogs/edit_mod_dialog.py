"""Diálogo para editar un mod de Factorio directamente.

Permite extraer el mod, editar sus archivos (info.json, data.lua, etc.)
y reconstruirlo todo desde una sola interfaz.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)

# Extensiones de archivo que se pueden editar como texto
EDITABLE_EXTENSIONS = {".json", ".lua", ".txt", ".md", ".csv", ".ini"}


class EditModDialog(QDialog):
    """Diálogo para editar un mod de Factorio directamente."""

    def __init__(self, plugin: FactorioPlugin, mod_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.mod_path = Path(mod_path)
        self._temp_dir: TemporaryDirectory | None = None
        self._extracted_dir: Path | None = None
        self._current_file: Path | None = None
        self.setWindowTitle(f"Editar mod: {self.mod_path.name}")
        self.resize(900, 700)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._setup_ui()
        self._extract_mod()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra de estado informativa
        info_label = QLabel(
            "Seleccione un archivo para editar. Los cambios se guardarán al reconstruir el mod."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Splitter para lista de archivos y editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Lista de archivos extraídos
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.files_list.setStyleSheet(
            "QListWidget::item { padding: 2px; margin: 0px; }"
        )
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        self.files_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.files_list)

        # Editor de texto
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Seleccione un archivo para editar...")
        self.editor.setStyleSheet(
            "QTextEdit { line-height: 1.2; padding: 4px; margin: 0px; }"
        )
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.editor)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(splitter)

        # Botones de acción
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("Guardar cambios")
        self.save_btn.clicked.connect(self._save_current_file)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.rebuild_btn = QPushButton("Reconstruir mod")
        self.rebuild_btn.clicked.connect(self._rebuild_mod)
        btn_layout.addWidget(self.rebuild_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _extract_mod(self) -> None:
        """Extrae el mod a un directorio temporal para edición."""
        try:
            self._temp_dir = TemporaryDirectory(prefix="modmaker_edit_")
            self._extracted_dir = Path(self._temp_dir.name) / "extracted"
            self._extracted_dir.mkdir(parents=True)

            if not zipfile.is_zipfile(self.mod_path):
                QMessageBox.critical(
                    self,
                    "Error",
                    "El archivo no es un ZIP válido.",
                )
                self.reject()
                return

            with zipfile.ZipFile(self.mod_path, "r") as zip_ref:
                zip_ref.extractall(self._extracted_dir)

            self._populate_files_list()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error extrayendo mod para editar: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo extraer el mod: {exc}",
            )
            self.reject()

    def _populate_files_list(self) -> None:
        """Llena la lista de archivos extraídos."""
        if not self._extracted_dir:
            return
        self.files_list.clear()
        for file_path in sorted(self._extracted_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(self._extracted_dir)
                item = QListWidgetItem(str(rel_path))
                item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                # Marcar archivos editables
                if file_path.suffix.lower() in EDITABLE_EXTENSIONS:
                    item.setText(f"[T] {rel_path}")
                self.files_list.addItem(item)

    def _on_file_selected(self) -> None:
        """Maneja la selección de un archivo en la lista."""
        item = self.files_list.currentItem()
        if not item:
            return

        file_path_str = item.data(Qt.ItemDataRole.UserRole)
        self._current_file = Path(file_path_str)

        # Verificar si es editable
        if self._current_file.suffix.lower() not in EDITABLE_EXTENSIONS:
            self.editor.setPlainText(
                f"Este archivo ({self._current_file.suffix}) no se puede editar desde esta interfaz."
            )
            self.editor.setReadOnly(True)
            self.save_btn.setEnabled(False)
            return

        try:
            content = self._current_file.read_text(encoding="utf-8")
            self.editor.setPlainText(content)
            self.editor.setReadOnly(False)
            self.save_btn.setEnabled(True)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error leyendo archivo: %s", exc)
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo leer el archivo: {exc}",
            )

    def _on_text_changed(self) -> None:
        """Marca que hay cambios sin guardar."""
        self.save_btn.setEnabled(True)

    def _save_current_file(self) -> None:
        """Guarda el archivo actualmente editado."""
        if not self._current_file:
            return
        try:
            self._current_file.write_text(
                self.editor.toPlainText(), encoding="utf-8"
            )
            self.save_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "Guardado",
                f"Cambios guardados en {self._current_file.name}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error guardando archivo: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el archivo: {exc}",
            )

    def _rebuild_mod(self) -> None:
        """Reconstruye el mod desde los archivos editados."""
        if not self._extracted_dir:
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar mod editado como",
            self.mod_path.name,
            "Archivos ZIP (*.zip)",
        )
        if not output_path:
            return

        output_path = Path(output_path)
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        try:
            self.plugin.build(self._extracted_dir, output_path)
            QMessageBox.information(
                self,
                "Mod reconstruido",
                f"El mod ha sido reconstruido en:\n{output_path}",
            )
            self.accept()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error reconstruyendo mod: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo reconstruir el mod: {exc}",
            )

    def closeEvent(self, event) -> None:  # noqa: N802
        # Limpiar directorio temporal
        if self._temp_dir:
            self._temp_dir.cleanup()
        super().closeEvent(event)
