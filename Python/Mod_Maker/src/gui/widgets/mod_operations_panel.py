"""Panel de operaciones de mod para Factorio_Mod_Maker.

Permite crear, extraer, reconstruir, instalar, desinstalar mods de Factorio,
configurar ruta de mods, crear items, tweaks, sprite sheets y exportar mods,
todo dentro de una pestaña integrada de la ventana principal (tipo VS Code).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.factorio_mod import FactorioMod, ModMetadata
from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.plugin_system import PluginSystem
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class ModOperationsPanel(QWidget):
    """Panel para gestionar mods de Factorio: crear, extraer, reconstruir,
    instalar, desinstalar, configurar ruta, crear items, tweaks, sprite sheets
    y exportar mods.

    Se usa como pestaña dentro de la ventana principal, al estilo de un IDE.
    """

    mod_created = Signal(str)
    mod_extracted = Signal(str)
    mod_rebuilt = Signal(str)
    mod_installed = Signal(str)
    mod_uninstalled = Signal(str)

    def __init__(
        self,
        plugin: FactorioPlugin,
        plugin_system: PluginSystem,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.plugin_system = plugin_system
        self.mod_name: str = "MyMod"
        self.current_mod_dir: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Barra de información
        self.info_label = QLabel(translate("mod_operations_panel.title"))
        self.info_label.setStyleSheet("color: #ffaa00; font-style: italic;")
        layout.addWidget(self.info_label)

        # Botones de acción (fila 1)
        btn_layout1 = QHBoxLayout()
        btn_layout1.setContentsMargins(0, 0, 0, 0)
        btn_layout1.setSpacing(5)

        self.create_mod_btn = QPushButton(translate("menu.mods.create"))
        self.create_mod_btn.clicked.connect(self._create_mod)
        btn_layout1.addWidget(self.create_mod_btn)

        self.extract_mod_btn = QPushButton(translate("dialog.extract_mod.title"))
        self.extract_mod_btn.clicked.connect(self._extract_mod)
        btn_layout1.addWidget(self.extract_mod_btn)

        self.rebuild_mod_btn = QPushButton(translate("dialog.rebuild_mod.build"))
        self.rebuild_mod_btn.clicked.connect(self._rebuild_mod)
        btn_layout1.addWidget(self.rebuild_mod_btn)

        btn_layout1.addStretch()
        layout.addLayout(btn_layout1)

        # Botones de acción (fila 2)
        btn_layout2 = QHBoxLayout()
        btn_layout2.setContentsMargins(0, 0, 0, 0)
        btn_layout2.setSpacing(5)

        self.config_path_btn = QPushButton(
            translate("dialog.manager.configure_path")
        )
        self.config_path_btn.clicked.connect(self._configure_mods_path)
        btn_layout2.addWidget(self.config_path_btn)

        self.new_item_btn = QPushButton(translate("menu.mods.new_item"))
        self.new_item_btn.clicked.connect(self._new_item)
        btn_layout2.addWidget(self.new_item_btn)

        self.tweaks_btn = QPushButton(translate("menu.mods.tweaks"))
        self.tweaks_btn.clicked.connect(self._tweaks)
        btn_layout2.addWidget(self.tweaks_btn)

        self.sprite_btn = QPushButton(translate("menu.mods.sprite_sheet"))
        self.sprite_btn.clicked.connect(self._sprite_sheet)
        btn_layout2.addWidget(self.sprite_btn)

        self.export_btn = QPushButton(translate("menu.mods.export_zip"))
        self.export_btn.clicked.connect(self._export_mod)
        btn_layout2.addWidget(self.export_btn)

        btn_layout2.addStretch()
        layout.addLayout(btn_layout2)

        # Botones de depuración (fila 3)
        btn_layout3 = QHBoxLayout()
        btn_layout3.setContentsMargins(0, 0, 0, 0)
        btn_layout3.setSpacing(5)

        self.debug_btn = QPushButton(translate("menu.mods.lua_editor"))
        self.debug_btn.clicked.connect(self._debug_mod)
        btn_layout3.addWidget(self.debug_btn)

        btn_layout3.addStretch()
        layout.addLayout(btn_layout3)

        # Espacio vacío al final
        layout.addStretch()

    def _find_tab_widget(self):
        """Busca el widget padre que tiene el QTabWidget (MainWindow)."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "tabs") and isinstance(parent.tabs, QTabWidget):
                return parent
            parent = parent.parent()
        return None

    def _add_as_tab(self, widget: QWidget, title: str) -> None:
        """Agrega un widget como pestaña en la ventana principal."""
        tabs_widget = self._find_tab_widget()
        if tabs_widget is None:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("dialog.debug_console.not_supported"),
            )
            return
        idx = tabs_widget.tabs.addTab(widget, title)
        tabs_widget.tabs.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def _create_mod(self) -> None:
        """Crear un mod nuevo."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.create_mod_dialog import CreateModDialog

        dialog = CreateModDialog(self.plugin, self)
        self._add_as_tab(dialog, translate("dialog.create_mod.title"))

    def _extract_mod(self) -> None:
        """Extraer un mod."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.extract_mod_dialog import ExtractModDialog

        dialog = ExtractModDialog(self.plugin, self)
        self._add_as_tab(dialog, translate("dialog.extract_mod.title"))

    def _rebuild_mod(self) -> None:
        """Reconstruir un mod."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.rebuild_mod_dialog import RebuildModDialog

        dialog = RebuildModDialog(self.plugin, self)
        self._add_as_tab(dialog, translate("dialog.rebuild_mod.build"))

    def _install_mod(self) -> None:
        """Instalar un mod."""
        from src.gui.dialogs.factorio_manager_dialog import FactorioManagerDialog

        dialog = FactorioManagerDialog(self.plugin, self.plugin_system, self)
        self._add_as_tab(dialog, translate("dialog.manager.title"))

    def _uninstall_mod(self) -> None:
        """Desinstalar un mod."""
        from src.gui.dialogs.factorio_manager_dialog import FactorioManagerDialog

        dialog = FactorioManagerDialog(self.plugin, self.plugin_system, self)
        self._add_as_tab(dialog, translate("dialog.manager.title"))

    def _new_item(self) -> None:
        """Crear un nuevo item de mod."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.new_item_dialog import NewItemDialog

        dialog = NewItemDialog(mod_name=self.mod_name, parent=self)
        self._add_as_tab(dialog, translate("factorio.new_item"))

    def _tweaks(self) -> None:
        """Abrir asistente de tweaks de gameplay."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.tweaks_dialog import TweaksDialog

        dialog = TweaksDialog(mod_name=self.mod_name, parent=self)
        self._add_as_tab(dialog, translate("factorio.tweaks"))

    def _sprite_sheet(self) -> None:
        """Abrir asistente de sprite sheet."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.sprite_sheet_dialog import SpriteSheetDialog

        dialog = SpriteSheetDialog(mod_name=self.mod_name, parent=self)
        self._add_as_tab(dialog, translate("factorio.sprite_sheet"))

    def _export_mod(self) -> None:
        """Exportar un mod a archivo .zip."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        from src.gui.dialogs.export_mod_dialog import ExportModDialog

        mod = FactorioMod(
            metadata=ModMetadata(
                name=self.mod_name,
                version="1.0.0",
            )
        )
        mod_dir = self.current_mod_dir or Path.cwd()
        dialog = ExportModDialog(mod=mod, mod_dir=mod_dir, parent=self)
        self._add_as_tab(dialog, translate("menu.mods.export_zip"))

    def _debug_mod(self) -> None:
        """Abrir consola de depuración Lua para seleccionar y depurar un mod."""
        if not self.plugin:
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("error.no_plugin", game="factorio"),
            )
            return

        if not self.plugin.is_debug_supported():
            QMessageBox.warning(
                self,
                translate("dialog.mod.error"),
                translate("dialog.debug_console.not_supported"),
            )
            return

        from src.gui.dialogs.debug_console_dialog import DebugConsoleDialog

        # Si hay un mod actual cargado, pasarlo como predeterminado;
        # de lo contrario, el usuario deberá seleccionar uno en el diálogo.
        mod_dir = self.current_mod_dir
        debug_panel = DebugConsoleDialog(self.plugin, mod_dir, self)
        self._add_as_tab(debug_panel, translate("menu.mods.lua_editor"))

    def _configure_mods_path(self) -> None:
        """Configurar ruta alternativa de mods de Factorio."""
        current = self.plugin_system.get_game_folder("factorio")
        new_path = QFileDialog.getExistingDirectory(
            self,
            translate("dialog.create_mod.select_folder"),
            str(current) if current else str(Path.cwd()),
        )
        if new_path:
            new_path = Path(new_path)
            try:
                self.plugin_system.set_game_folder("factorio", new_path)
                QMessageBox.information(
                    self,
                    translate("dialog.create_mod.title"),
                    translate("status.mods_folder_updated", path=new_path),
                )
                self.info_label.setText(
                    f"Carpeta de mods: {new_path}"
                )
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("Error configurando ruta de mods: %s", exc)
                QMessageBox.critical(
                    self,
                    translate("dialog.create_mod.title"),
                    f"No se pudo configurar la ruta: {exc}",
                )

    def refresh_mods(self) -> None:
        """Refrescar la información de la carpeta de mods detectada."""
        mods_folder = self.plugin_system.get_game_folder("factorio")
        if mods_folder:
            self.info_label.setText(
                f"Carpeta de mods: {mods_folder}"
            )
            self.info_label.setStyleSheet(
                "color: #aaaa00; font-style: italic;"
            )
        else:
            self.info_label.setText(
                translate("status.mods_folder_not_detected")
            )
            self.info_label.setStyleSheet(
                "color: #ff6666; font-style: italic;"
            )
