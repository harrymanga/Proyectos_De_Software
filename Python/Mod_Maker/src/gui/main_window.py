"""Ventana principal de Mod_Maker.

Interfaz tipo IDE (VS Code):
- Panel izquierdo: explorador de mods instalados.
- Panel derecho: pestañas con operaciones por juego.
- Los diálogos modales se evitan; todo se gestiona dentro de la ventana.

Norma §58: temas claro/oscuro explícitos, hilos para I/O, QSettings,
log + statusbar, menús base.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from src.core.config import ConfigManager
from src.core.factorio_mod import FactorioMod, ModMetadata
from src.core.i18n import i18n, translate
from src.core.logger import get_logger
from src.core.plugin_system import PluginSystem
from src.gui.dialogs import (
    CreateModDialog,
    ExportModDialog,
    NewItemDialog,
    SpriteSheetDialog,
    TweaksDialog,
)
from src.gui.widgets.edit_mod_tab import EditModTab
from src.gui.widgets.mod_operations_panel import ModOperationsPanel
from src.gui.widgets.mods_explorer_panel import ModsExplorerPanel
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class WorkerThread(QThread):
    """Hilo de trabajo para operaciones de I/O largas (no bloquean la GUI)."""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, func, *args, **kwargs) -> None:
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(str(result) if result else "")
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error en hilo de trabajo: %s", exc)
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Ventana principal con layout tipo IDE (explorador + pestañas).

    Las pestañas de gestión de juegos se abren solo cuando el usuario
    selecciona un juego del menú "Juegos". No hay pestañas abiertas
    por defecto.
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.plugin_system = PluginSystem()
        self.factorio_plugin: FactorioPlugin | None = (
            self.plugin_system.get_plugin("factorio")
        )
        self.current_mod: FactorioMod | None = None
        self.current_mod_dir: Path | None = None
        self.mod_name: str = "MyMod"
        self._edit_tabs: dict[str, int] = {}  # ruta_mod -> índice de pestaña
        self._game_tabs: dict[str, int] = {}  # game_id -> índice de pestaña

        self.setWindowTitle(translate("app.title"))
        self.resize(
            self.config.get("app", "window_width", 1200),
            self.config.get("app", "window_height", 800),
        )
        self._setup_ui()
        self._apply_theme()
        self.statusBar().showMessage(translate("status.ready"))

    def _setup_ui(self) -> None:
        # Splitter principal: explorador izquierda, pestañas derecha
        splitter = self._create_splitter()
        self.setCentralWidget(splitter)

        self._create_menu_bar()
        self._create_status_bar()

    def _create_splitter(self) -> QWidget:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: explorador de mods
        self.explorer_panel = ModsExplorerPanel(self.plugin_system, self)
        self.explorer_panel.setMinimumWidth(260)
        self.explorer_panel.setMaximumWidth(400)
        self.explorer_panel.mod_selected.connect(self._open_edit_tab)
        splitter.addWidget(self.explorer_panel)

        # Panel derecho: pestañas de operaciones (inicialmente vacío)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        splitter.addWidget(self.tabs)

        # Proporción: 30% explorador, 70% pestañas
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        return splitter

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # Archivo
        file_menu = menu_bar.addMenu(translate("menu.file"))
        exit_action = QAction(translate("menu.file.exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Juegos (aquí se abren las pestañas de gestión de cada juego)
        games_menu = menu_bar.addMenu(translate("menu.games"))
        factorio_action = QAction(translate("menu.games.factorio"), self)
        factorio_action.triggered.connect(self._open_factorio_manager)
        games_menu.addAction(factorio_action)

        # Configuración
        settings_menu = menu_bar.addMenu(translate("menu.settings"))
        lang_menu = settings_menu.addMenu(translate("menu.language"))
        for lang_code in i18n.get_available_languages():
            label = "Español" if lang_code == "es" else "English"
            action = QAction(label, self)
            action.triggered.connect(lambda checked, c=lang_code: self._set_language(c))
            lang_menu.addAction(action)

        theme_menu = settings_menu.addMenu(translate("menu.theme"))
        light_action = QAction(translate("theme.light"), self)
        light_action.triggered.connect(lambda: self._set_theme("light"))
        dark_action = QAction(translate("theme.dark"), self)
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)

        # Ayuda
        help_menu = menu_bar.addMenu(translate("menu.help"))
        about_action = QAction(translate("menu.help.about"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(translate("status.ready"))

    def _apply_theme(self) -> None:
        theme = self.config.get("app", "theme", "dark")
        if theme == "light":
            self.setStyleSheet("")
        else:
            self.setStyleSheet(
                "QMainWindow { background-color: #2b2b2b; color: #ffffff; }"
                "QTabWidget::pane { border: 1px solid #555555; }"
                "QMenuBar { background-color: #3c3c3c; color: #ffffff; }"
                "QMenuBar::item:selected { background-color: #555555; }"
                "QStatusBar { background-color: #3c3c3c; color: #ffffff; }"
                "QSplitter::handle { background-color: #555555; }"
            )

    def _set_language(self, language: str) -> None:
        i18n.set_language(language)
        self.config.set("app", "language", language)
        self.setWindowTitle(translate("app.title"))
        self.status_bar.showMessage(translate("status.ready"))
        QMessageBox.information(
            self,
            translate("app.title"),
            "El idioma se ha cambiado. Reinicie la aplicación para aplicar todos los textos.",
        )

    def _set_theme(self, theme: str) -> None:
        self.config.set("app", "theme", theme)
        self._apply_theme()

    def _require_factorio_plugin(self) -> bool:
        if self.factorio_plugin is None:
            QMessageBox.warning(
                self,
                translate("error.no_plugin", game="factorio"),
                translate("error.no_plugin", game="factorio"),
            )
            return False
        return True

    def _open_factorio_manager(self) -> None:
        """Abre la pestaña de gestión de mods de Factorio."""
        if not self._require_factorio_plugin():
            return

        # Si ya existe la pestaña, solo cambiar a ella
        if "factorio" in self._game_tabs:
            idx = self._game_tabs["factorio"]
            self.tabs.setCurrentIndex(idx)
            return

        # Crear la pestaña de gestión de mods de Factorio
        self.ops_panel = ModOperationsPanel(
            self.factorio_plugin, self.plugin_system, self
        )
        self.ops_panel.mod_created.connect(self._on_mod_created)
        self.ops_panel.mod_extracted.connect(self._on_mod_extracted)
        self.ops_panel.mod_rebuilt.connect(self._on_mod_rebuilt)
        self.ops_panel.mod_installed.connect(self._on_mod_installed)
        self.ops_panel.mod_uninstalled.connect(self._on_mod_uninstalled)

        idx = self.tabs.addTab(
            self.ops_panel, translate("menu.games.factorio")
        )
        self.tabs.setCurrentIndex(idx)
        self._game_tabs["factorio"] = idx
        self.ops_panel.refresh_mods()
        self.explorer_panel.refresh_mods()

    def _open_edit_tab(self, mod_path: str) -> None:
        """Abre una pestaña para editar el mod seleccionado."""
        if not self._require_factorio_plugin():
            return

        mod_path_str = str(mod_path)
        if mod_path_str in self._edit_tabs:
            idx = self._edit_tabs[mod_path_str]
            self.tabs.setCurrentIndex(idx)
            return

        # Crear pestaña de edición
        tab_widget = EditModTab(self.factorio_plugin, Path(mod_path_str), self)
        tab_widget.mod_rebuilt.connect(self._on_mod_rebuilt)
        tab_widget.tab_closed.connect(self._on_edit_tab_closed)

        idx = self.tabs.addTab(tab_widget, Path(mod_path).name)
        self.tabs.setCurrentIndex(idx)
        self._edit_tabs[mod_path_str] = idx

    def _on_edit_tab_closed(self) -> None:
        """Maneja el cierre de una pestaña de edición."""
        idx = self.tabs.currentIndex()
        if idx > 0:  # No cerrar la pestaña principal (índice 0)
            widget = self.tabs.widget(idx)
            widget.deleteLater()
            self.tabs.removeTab(idx)
            # Limpiar _edit_tabs
            mod_path_str = None
            for key, val in list(self._edit_tabs.items()):
                if val == idx:
                    mod_path_str = key
                    break
            if mod_path_str:
                del self._edit_tabs[mod_path_str]
            # Reindexar
            for i in range(self.tabs.count()):
                _ = self.tabs.widget(i)
                for key, val in self._edit_tabs.items():
                    if val > i:
                        self._edit_tabs[key] = val - 1

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget is self.ops_panel:
            return  # No cerrar la pestaña de gestión de juegos
        widget.deleteLater()
        self.tabs.removeTab(index)
        # Limpiar _edit_tabs
        mod_path_str = None
        for key, val in list(self._edit_tabs.items()):
            if val == index:
                mod_path_str = key
                break
        if mod_path_str:
            del self._edit_tabs[mod_path_str]
        # Reindexar
        for i in range(self.tabs.count()):
            _ = self.tabs.widget(i)
            for key, val in self._edit_tabs.items():
                if val > i:
                    self._edit_tabs[key] = val - 1

    def _create_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = CreateModDialog(self.factorio_plugin, self)
        dialog.exec()
        self.ops_panel.refresh_mods()
        self.explorer_panel.refresh_mods()

    def _extract_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        self.ops_panel._extract_mod()
        self.explorer_panel.refresh_mods()

    def _rebuild_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        self.ops_panel._rebuild_mod()
        self.explorer_panel.refresh_mods()

    def _open_factorio_manager_old(self) -> None:
        """Método legacy mantenido por compatibilidad."""
        self._open_factorio_manager()

    def _new_item(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = NewItemDialog(mod_name=self.mod_name, parent=self)
        dialog.exec()

    def _tweaks(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = TweaksDialog(mod_name=self.mod_name, parent=self)
        dialog.exec()

    def _sprite_sheet(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = SpriteSheetDialog(mod_name=self.mod_name, parent=self)
        dialog.exec()

    def _export_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        mod = self.current_mod or FactorioMod(
            metadata=ModMetadata(name="MyMod", version="1.0.0")
        )
        dialog = ExportModDialog(mod=mod, mod_dir=self.current_mod_dir, parent=self)
        dialog.exec()

    def _lua_editor(self) -> None:
        if not self._require_factorio_plugin():
            return
        QMessageBox.information(
            self,
            translate("factorio.lua_editor"),
            "El editor Lua estará disponible en la próxima fase de implementación.",
        )

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            translate("about.title"),
            translate("about.text"),
        )

    def _on_mod_created(self, name: str) -> None:
        self.status_bar.showMessage(f"Mod creado: {name}")
        self.explorer_panel.refresh_mods()

    def _on_mod_extracted(self, dest: str) -> None:
        self.status_bar.showMessage(f"Mod extraído: {dest}")

    def _on_mod_rebuilt(self, output: str) -> None:
        self.status_bar.showMessage(f"Mod reconstruido: {output}")
        self.explorer_panel.refresh_mods()

    def _on_mod_installed(self, name: str) -> None:
        self.status_bar.showMessage(f"Mod instalado: {name}")
        self.explorer_panel.refresh_mods()

    def _on_mod_uninstalled(self, name: str) -> None:
        self.status_bar.showMessage(f"Mod desinstalado: {name}")
        self.explorer_panel.refresh_mods()

    def closeEvent(self, event) -> None:
        self.config.set("app", "window_width", self.width())
        self.config.set("app", "window_height", self.height())
        super().closeEvent(event)


def main() -> None:
    """Punto de entrada de la aplicación GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("Mod_Maker")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
