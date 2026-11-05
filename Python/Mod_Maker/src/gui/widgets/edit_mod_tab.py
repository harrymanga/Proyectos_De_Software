"""Diálogo para editar un mod de Factorio directamente.

Permite extraer, editar archivos (info.json, data.lua, etc.) y reconstruir el mod,
todo dentro de una pestaña de la ventana principal (tipo VS Code).

Incluye:
- Árbol de archivos (tree view) tipo VS Code
- Menú contextual (clic derecho) para crear/eliminar/renombrar
- Crear archivos y carpetas en la ubicación seleccionada
- Vista previa de imágenes
- Syntax highlighting para múltiples lenguajes
- Guardar y reconstruir mods
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.mod_file_manager import ModFileManager
from src.core.syntax_highlighter import SyntaxHighlighterFactory
from src.gui.widgets.lua_completer import LuaCompleter
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)

# Extensiones de archivo que se pueden editar como texto
EDITABLE_EXTENSIONS = {
    ".json", ".lua", ".txt", ".md", ".csv", ".ini", ".cfg", ".toml",
}

# Extensiones de imagen que se pueden previsualizar
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tga"}


class EditModTab(QWidget):
    """Pestaña para editar un mod de Factorio directamente.

    Permite extraer el mod, editar sus archivos, crear/eliminar archivos y carpetas,
    renombrar elementos y reconstruir el mod,
    todo dentro de una pestaña de la ventana principal (tipo VS Code).
    """

    mod_rebuilt = Signal(str)
    tab_closed = Signal()

    def __init__(
        self,
        plugin: FactorioPlugin,
        mod_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.mod_path = Path(mod_path)
        self._temp_dir: TemporaryDirectory | None = None
        self._extracted_dir: Path | None = None
        self._source_dir: Path | None = None
        self._current_file: Path | None = None
        self._highlighter = None
        self.file_manager: ModFileManager | None = None
        self._current_item: QTreeWidgetItem | None = None
        self.setWindowTitle(f"Editar mod: {self.mod_path.name}")
        self._setup_ui()
        self._extract_mod()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Barra de información
        self.info_label = QLabel(f"Editando: {self.mod_path.name}")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #ffaa00; font-style: italic;")
        layout.addWidget(self.info_label)

        # Splitter para lista de archivos, editor y vista previa
        from PySide6.QtWidgets import QSplitter

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Lista de archivos extraídos (árbol tipo VS Code)
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabel("Archivos")
        self.files_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.files_tree.itemSelectionChanged.connect(self._on_file_selected)
        self.files_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.files_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.files_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.files_tree)

        # Editor de texto y vista previa (splitter vertical)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Editor de texto
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Seleccione un archivo para editar...")
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_splitter.addWidget(self.editor)

        # Conectar autocompletado de Lua
        self.lua_completer = LuaCompleter(self.editor)
        self.lua_completer.attach(self.editor)

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
        self.close_btn.clicked.connect(self._close_tab)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Barra de estado
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _show_context_menu(self, position) -> None:
        """Muestra menú contextual al hacer clic derecho en un archivo."""
        item = self.files_tree.itemAt(position)
        if item is None:
            # Menú para crear en la raíz
            menu = QMenu(self)
            new_file_action = menu.addAction(translate("dialog.mod.create_new_file"))
            new_folder_action = menu.addAction(translate("dialog.mod.create_new_folder"))
            new_file_action.triggered.connect(
                lambda: self._create_new_file_in_folder("")
            )
            new_folder_action.triggered.connect(
                lambda: self._create_new_folder_in_folder("")
            )
            menu.exec(self.files_tree.mapToGlobal(position))
            return

        # Obtener la ruta relativa del elemento seleccionado
        file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_path_str:
            return

        current_path = Path(file_path_str)
        is_folder = item.data(0, Qt.ItemDataRole.UserRole + 1)

        menu = QMenu(self)

        if is_folder:
            # Opciones para carpeta
            new_file_action = menu.addAction(translate("dialog.mod.create_new_file"))
            new_folder_action = menu.addAction(translate("dialog.mod.create_new_folder"))
            rename_action = menu.addAction(translate("dialog.mod.rename"))
            delete_action = menu.addAction(translate("dialog.mod.delete"))

            new_file_action.triggered.connect(
                lambda: self._create_new_file_in_folder(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
            new_folder_action.triggered.connect(
                lambda: self._create_new_folder_in_folder(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
            rename_action.triggered.connect(
                lambda: self._rename_item(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
            delete_action.triggered.connect(
                lambda: self._delete_item(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
        else:
            # Opciones para archivo
            rename_action = menu.addAction(translate("dialog.mod.rename"))
            delete_action = menu.addAction(translate("dialog.mod.delete"))
            new_file_action = menu.addAction(translate("dialog.mod.create_new_file"))
            new_folder_action = menu.addAction(translate("dialog.mod.create_new_folder"))

            # Para crear en la misma carpeta que el archivo seleccionado
            parent_path = str(current_path.relative_to(self._source_dir or self._extracted_dir).parent)
            if str(parent_path) == ".":
                parent_path = ""

            rename_action.triggered.connect(
                lambda: self._rename_item(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
            delete_action.triggered.connect(
                lambda: self._delete_item(str(current_path.relative_to(self._source_dir or self._extracted_dir)))
            )
            new_file_action.triggered.connect(
                lambda: self._create_new_file_in_folder(parent_path)
            )
            new_folder_action.triggered.connect(
                lambda: self._create_new_folder_in_folder(parent_path)
            )

        menu.exec(self.files_tree.mapToGlobal(position))

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
                self._close_tab()
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

            # Inicializar gestor de archivos
            self.file_manager = ModFileManager(self._source_dir)

            self._populate_files_list()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error extrayendo mod para editar: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo extraer el mod: {exc}",
            )
            self._close_tab()

    def _populate_files_list(self) -> None:
        """Llena la lista de archivos extraídos en forma de árbol."""
        if not self._extracted_dir:
            return
        self.files_tree.clear()

        def add_items(parent_item: QTreeWidgetItem, dir_path: Path) -> None:
            try:
                items = sorted(dir_path.iterdir())
            except PermissionError:
                return
            for item_path in items:
                rel_path = item_path.relative_to(self._extracted_dir)
                item = QTreeWidgetItem(parent_item)
                item.setText(0, item_path.name)
                item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))

                if item_path.is_dir():
                    item.setText(0, f"📁 {item_path.name}")
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, True)  # Es carpeta
                    item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))  # Ruta relativa
                    add_items(item, item_path)
                elif item_path.suffix.lower() in EDITABLE_EXTENSIONS:
                    item.setText(0, f"📄 {item_path.name}")
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, False)  # Es archivo editable
                    item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))
                elif item_path.suffix.lower() in IMAGE_EXTENSIONS:
                    item.setText(0, f"🖼️ {item_path.name}")
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                    item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))
                else:
                    item.setText(0, f"📎 {item_path.name}")
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                    item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))

                self.files_tree.addTopLevelItem(item)

        self._populate_tree_recursive(self._extracted_dir, self.files_tree)

    def _populate_tree_recursive(self, dir_path: Path, parent_item: QTreeWidgetItem) -> None:
        """Llena recursivamente el árbol de archivos."""
        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        for item_path in items:
            rel_path = item_path.relative_to(self._extracted_dir)
            item = QTreeWidgetItem(parent_item)
            item.setText(0, item_path.name)
            item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))

            if item_path.is_dir():
                item.setText(0, f"📁 {item_path.name}")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, True)
                item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))
                self._populate_tree_recursive(item_path, item)
            elif item_path.suffix.lower() in EDITABLE_EXTENSIONS:
                item.setText(0, f"📄 {item_path.name}")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))
            elif item_path.suffix.lower() in IMAGE_EXTENSIONS:
                item.setText(0, f"🖼️ {item_path.name}")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))
            else:
                item.setText(0, f"📎 {item_path.name}")
                item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                item.setData(0, Qt.ItemDataRole.UserRole + 2, str(rel_path))

    def _get_current_item_rel_path(self) -> str:
        """Obtiene la ruta relativa del elemento seleccionado."""
        item = self.files_tree.currentItem()
        if not item:
            return ""
        rel_path = item.data(0, Qt.ItemDataRole.UserRole + 2)
        if rel_path:
            return rel_path
        # Fallback: calcular desde el path completo
        file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path_str:
            try:
                return str(Path(file_path_str).relative_to(self._source_dir or self._extracted_dir))
            except ValueError:
                return str(file_path_str)
        return ""

    def _on_file_selected(self) -> None:
        """Maneja la selección de un archivo en la lista."""
        item = self.files_tree.currentItem()
        if not item:
            self._reset_editor_state()
            return

        file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        is_folder = item.data(0, Qt.ItemDataRole.UserRole + 1)

        if is_folder:
            self.editor.setVisible(False)
            self.preview_panel.setVisible(False)
            self.save_btn.setEnabled(False)
            self._current_file = None
            self.lua_completer.setEnabled(False)
            return

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
                # Activar autocompletado solo para archivos .lua
                if ext == ".lua":
                    self.lua_completer.setEnabled(True)
                    self.editor.setFocus()  # Dar foco al editor para autocomplete
                else:
                    self.lua_completer.setEnabled(False)
            except Exception as exc:
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
                            300, 200,
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
            except Exception as exc:
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
            self.lua_completer.setEnabled(False)

    def _reset_editor_state(self) -> None:
        """Reseta el estado del editor cuando no hay selección."""
        self.editor.setVisible(False)
        self.preview_panel.setVisible(False)
        self.save_btn.setEnabled(False)
        self.lua_completer.setEnabled(False)
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
        except Exception as exc:
            logger.error("Error guardando archivo: %s", exc)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el archivo: {exc}",
            )

    def _create_new_file_in_folder(self, rel_folder: str) -> None:
        """Crea un nuevo archivo en la carpeta especificada."""
        if not self.file_manager:
            return

        file_name, ok = QInputDialog.getText(
            self,
            translate("dialog.mod.create_new_file"),
            translate("dialog.mod.file_name"),
        )
        if not ok or not file_name.strip():
            return

        file_name = file_name.strip()

        import re
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', file_name):
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("dialog.mod.invalid_name"),
            )
            return

        target_path = Path(rel_folder) / file_name if rel_folder else Path(file_name)

        try:
            self.file_manager.create_file(str(target_path), "")
            self._populate_files_list()
            self.status_label.setText(f"Archivo creado: {file_name}")
        except Exception as exc:
            logger.error("Error creando archivo: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.mod.error"),
                f"No se pudo crear el archivo: {exc}",
            )

    def _create_new_folder_in_folder(self, rel_folder: str) -> None:
        """Crea una nueva carpeta en la carpeta especificada."""
        if not self.file_manager:
            return

        folder_name, ok = QInputDialog.getText(
            self,
            translate("dialog.mod.create_new_folder"),
            translate("dialog.mod.folder_name"),
        )
        if not ok or not folder_name.strip():
            return

        folder_name = folder_name.strip()

        import re
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', folder_name):
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("dialog.mod.invalid_name"),
            )
            return

        target_path = Path(rel_folder) / folder_name if rel_folder else Path(folder_name)

        try:
            self.file_manager.create_folder(str(target_path))
            self._populate_files_list()
            self.status_label.setText(f"Carpeta creada: {folder_name}")
        except Exception as exc:
            logger.error("Error creando carpeta: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.mod.error"),
                f"No se pudo crear la carpeta: {exc}",
            )

    def _rename_item(self, rel_path: str | None = None) -> None:
        """Renombra el archivo o carpeta seleccionada."""
        item = self.files_tree.currentItem()
        if not item:
            return

        if rel_path is None:
            rel_path = item.data(0, Qt.ItemDataRole.UserRole + 2)
            if not rel_path:
                file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
                if file_path_str:
                    try:
                        rel_path = str(Path(file_path_str).relative_to(self._source_dir or self._extracted_dir))
                    except ValueError:
                        rel_path = str(file_path_str)

        current_name = Path(rel_path).name

        new_name, ok = QInputDialog.getText(
            self,
            translate("dialog.mod.rename"),
            translate("dialog.mod.new_name"),
            text=current_name,
        )
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()

        import re
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', new_name):
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("dialog.mod.invalid_name"),
            )
            return

        try:
            if item.data(0, Qt.ItemDataRole.UserRole + 1):  # Es carpeta
                self.file_manager.rename_folder(rel_path, new_name)
            else:
                self.file_manager.rename_file(rel_path, new_name)
            self._populate_files_list()
            self.status_label.setText(f"Renombrado: {new_name}")
        except Exception as exc:
            logger.error("Error renombrando: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.mod.error"),
                f"No se pudo renombrar: {exc}",
            )

    def _delete_item(self, rel_path: str | None = None) -> None:
        """Elimina el archivo o carpeta seleccionada."""
        item = self.files_tree.currentItem()
        if not item:
            return

        if rel_path is None:
            rel_path = item.data(0, Qt.ItemDataRole.UserRole + 2)
            if not rel_path:
                file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
                if file_path_str:
                    try:
                        rel_path = str(Path(file_path_str).relative_to(self._source_dir or self._extracted_dir))
                    except ValueError:
                        rel_path = str(file_path_str)

        item_name = Path(rel_path).name

        confirm = QMessageBox.question(
            self,
            translate("dialog.mod.confirm_delete"),
            translate("dialog.mod.confirm_delete_msg", name=item_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            if item.data(0, Qt.ItemDataRole.UserRole + 1):
                self.file_manager.delete_folder(rel_path)
            else:
                self.file_manager.delete_file(rel_path)
            self._populate_files_list()
            self.status_label.setText(f"Eliminado: {item_name}")
        except Exception as exc:
            logger.error("Error eliminando: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.mod.error"),
                f"No se pudo eliminar: {exc}",
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
            self.status_label.setText(
                f"Mod reconstruido en: {output_path}"
            )
            self.mod_rebuilt.emit(str(output_path))
            QMessageBox.information(
                self,
                translate("dialog.rebuild_mod.title"),
                f"Mod reconstruido correctamente en:\n{output_path}",
            )
        except Exception as exc:
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
        self.tab_closed.emit()
        self.deleteLater()
