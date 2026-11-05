"""Diálogo para editar archivos Lua de mods de Factorio.

Proporciona:
- Editor de texto con sintaxis highlighting para Lua
- Autocompletado de API de Factorio (funciones, eventos, tipos)
- Vista previa de archivos
- Guardado y reconstrucción de mods
- Integración con el sistema de plugins de Factorio
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
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
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.mod_file_manager import ModFileManager
from src.core.syntax_highlighter import SyntaxHighlighterFactory
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)

# Extensiones de archivo que se pueden editar como texto
EDITABLE_EXTENSIONS = {
    ".json",
    ".lua",
    ".txt",
    ".md",
    ".csv",
    ".ini",
    ".cfg",
    ".toml",
}

# Extensiones de imagen que se pueden previsualizar
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tga"}


class LuaEditorDialog(QDialog):
    """Diálogo para editar un mod de Factorio directamente.

    Permite extraer, editar archivos (info.json, data.lua, etc.) y reconstruir
    el mod, todo dentro de una ventana independiente.
    """

    def __init__(
        self,
        plugin: FactorioPlugin,
        mod_path: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.mod_path = Path(mod_path) if mod_path else None
        self._temp_dir: TemporaryDirectory | None = None
        self._extracted_dir: Path | None = None
        self._source_dir: Path | None = None
        self._current_file: Path | None = None
        self._highlighter = None
        self.file_manager: object | None = None
        self.setWindowTitle(f"Editar mod: {self.mod_path.name}")
        self.resize(900, 700)
        self._setup_ui()
        self._extract_mod()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra de información
        self.info_label = QLabel(f"Editando: {self.mod_path.name}")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #ffaa00; font-style: italic;")
        layout.addWidget(self.info_label)

        # Splitter para lista de archivos y editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Lista de archivos extraídos (árbol tipo VS Code)
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        self.files_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.files_list)

        # Editor de texto
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Seleccione un archivo para editar...")
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.editor)

        # Panel de vista previa de imágenes
        self.preview_panel = QWidget()
        preview_layout = QVBoxLayout(self.preview_panel)
        self.preview_label = QLabel("")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #2b2b2b;")
        self.preview_label.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_label)
        self.preview_info = QLabel("")
        self.preview_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_info.setStyleSheet("color: #888; font-size: 11px;")
        preview_layout.addWidget(self.preview_info)
        preview_layout.addStretch()
        right_splitter.addWidget(self.preview_panel)

        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        splitter.addWidget(right_splitter)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(splitter)

        # Botones de acción
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton(translate("dialog.manager.save_changes"))
        self.save_btn.clicked.connect(self._save_current_file)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.rebuild_btn = QPushButton(translate("dialog.rebuild_mod.build"))
        self.rebuild_btn.clicked.connect(self._rebuild_mod)
        btn_layout.addWidget(self.rebuild_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton(translate("menu.file.exit"))
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Barra de estado
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

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

            # Detectar la carpeta contenedora del mod
            info_files = []
            for f in self._extracted_dir.rglob("*"):
                if f.is_file() and f.name.lower() == "info.json":
                    info_files.append(f)

            if info_files:
                self._source_dir = info_files[0].parent
                logger.info(
                    "Carpeta de mod detectada: %s",
                    self._source_dir,
                )
            else:
                self._source_dir = self._extracted_dir
                logger.warning(
                    "No se encontró info.json en %s; usando carpeta raíz",
                    self._extracted_dir,
                )

            self.file_manager = ModFileManager(self._source_dir)
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
                elif file_path.suffix.lower() in IMAGE_EXTENSIONS:
                    item.setText(f"[I] {rel_path}")
                else:
                    item.setText(f"[ ] {rel_path}")
                self.files_list.addItem(item)

    def _on_file_selected(self) -> None:
        """Maneja la selección de un archivo en la lista."""
        item = self.files_list.currentItem()
        if not item:
            self._reset_editor_state()
            return

        file_path_str = item.data(Qt.ItemDataRole.UserRole)
        self._current_file = Path(file_path_str)
        ext = self._current_file.suffix.lower()

        self.editor.setVisible(False)
        self.preview_panel.setVisible(False)

        if ext in EDITABLE_EXTENSIONS:
            try:
                content = self._current_file.read_text(encoding="utf-8")
                self.editor.setPlainText(content)
                self.editor.setReadOnly(False)
                self.save_btn.setEnabled(True)
                self.editor.setVisible(True)
                self._apply_syntax_highlighter()
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("Error leyendo archivo: %s", exc)
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo leer el archivo: {exc}",
                )
        elif ext in IMAGE_EXTENSIONS:
            try:
                pixmap = QPixmap(str(self._current_file))
                if not pixmap.isNull():
                    self.preview_label.setPixmap(
                        pixmap.scaled(
                            300,
                            200,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                    self.preview_info.setText(
                        f"{self._current_file.name}\n"
                        f"{pixmap.width()} x {pixmap.height()} píxeles"
                    )
                    self.preview_panel.setVisible(True)
                    self.save_btn.setEnabled(False)
                else:
                    self.preview_label.setText("No se pudo cargar la imagen")
                    self.preview_info.setText("")
                    self.preview_panel.setVisible(True)
                    self.save_btn.setEnabled(False)
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("Error cargando imagen: %s", exc)
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo cargar la imagen: {exc}",
                )
        else:
            self.editor.setPlainText(
                f"Este archivo ({self._current_file.suffix}) no se puede editar desde esta interfaz."
            )
            self.editor.setReadOnly(True)
            self.save_btn.setEnabled(False)
            self.editor.setVisible(True)

    def _reset_editor_state(self) -> None:
        """Reseta el estado del editor cuando no hay selección."""
        self.editor.setVisible(False)
        self.preview_panel.setVisible(False)
        self.save_btn.setEnabled(False)
        self._current_file = None

    def _apply_syntax_highlighter(self) -> None:
        """Aplica el resaltador de sintaxis apropiado según el archivo."""
        if self._highlighter is not None:
            self._highlighter.setDocument(None)
            self._highlighter = None

        if self._current_file is None:
            return

        ext = self._current_file.suffix.lower()
        if ext in EDITABLE_EXTENSIONS:
            self._highlighter = SyntaxHighlighterFactory.create(
                self.editor.document(), str(self._current_file)
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
        if not self._source_dir:
            QMessageBox.warning(
                self,
                translate("dialog.rebuild_mod.title"),
                "No hay carpeta de mod válida para reconstruir.",
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar mod reconstruido como",
            self.mod_path.name,
            "Archivos ZIP (*.zip)",
        )
        if not output_path:
            return

        output_path = Path(output_path)
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        try:
            self.plugin.build(self._source_dir, output_path)
            self.status_label.setText(f"Mod reconstruido en: {output_path}")
            QMessageBox.information(
                self,
                translate("dialog.rebuild_mod.title"),
                f"Mod reconstruido correctamente en:\n{output_path}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error reconstruyendo mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.rebuild_mod.title"),
                f"No se pudo reconstruir el mod: {exc}",
            )

    def _close_tab(self) -> None:
        """Cierra la pestaña y limpia recursos."""
        if self._temp_dir:
            self._temp_dir.cleanup()
        self.deleteLater()