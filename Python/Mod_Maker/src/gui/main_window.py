"""Ventana principal de Mod_Maker.

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
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from src.core.config import ConfigManager
from src.core.i18n import i18n, translate
from src.core.logger import get_logger
from src.core.manager import ModManager
from src.core.plugin_system import PluginSystem
from src.core.worker import run_in_background
from src.gui.dialogs import (
    CreateModDialog,
    ExtractModDialog,
    FactorioManagerDialog,
    RebuildModDialog,
)
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

    def run(self) -> None:  # noqa: D401
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(str(result) if result else "")
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error en hilo de trabajo: %s", exc)
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Ventana principal con menús base, barra de estado y pestañas."""

    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.plugin_system = PluginSystem()
        self.factorio_plugin: FactorioPlugin | None = (
            self.plugin_system.get_plugin("factorio")
        )
        self.setWindowTitle(translate("app.title"))
        self.resize(
            self.config.get("app", "window_width", 1024),
            self.config.get("app", "window_height", 768),
        )
        self._setup_ui()
        self._apply_theme()
        self.statusBar().showMessage(translate("status.ready"))

    def _setup_ui(self) -> None:
        central = QTabWidget()
        self.setCentralWidget(central)

        # Pestaña principal vacía (se rellenará en fases posteriores)
        placeholder = QWidget()
        central.addTab(placeholder, translate("menu.games.factorio"))

        self._create_menu_bar()
        self._create_status_bar()

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # Archivo
        file_menu = menu_bar.addMenu(translate("menu.file"))
        exit_action = QAction(translate("menu.file.exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Juegos
        games_menu = menu_bar.addMenu(translate("menu.games"))
        factorio_action = QAction(translate("menu.games.factorio"), self)
        factorio_action.triggered.connect(self._open_factorio_manager)
        games_menu.addAction(factorio_action)

        # Mods
        mods_menu = menu_bar.addMenu(translate("menu.mods"))
        create_action = QAction(translate("menu.mods.create"), self)
        create_action.triggered.connect(self._create_mod)
        extract_action = QAction(translate("menu.mods.extract"), self)
        extract_action.triggered.connect(self._extract_mod)
        rebuild_action = QAction(translate("menu.mods.rebuild"), self)
        rebuild_action.triggered.connect(self._rebuild_mod)
        mods_menu.addAction(create_action)
        mods_menu.addAction(extract_action)
        mods_menu.addAction(rebuild_action)
        mods_menu.addSeparator()
        manager_action = QAction(translate("menu.mods.manager"), self)
        manager_action.triggered.connect(self._open_factorio_manager)
        mods_menu.addAction(manager_action)

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
        """Verifica que el plugin de Factorio esté disponible."""
        if self.factorio_plugin is None:
            QMessageBox.warning(
                self,
                translate("error.no_plugin", game="factorio"),
                translate("error.no_plugin", game="factorio"),
            )
            return False
        return True

    def _create_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = CreateModDialog(self.factorio_plugin, self)
        dialog.exec()

    def _extract_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = ExtractModDialog(self.factorio_plugin, self)
        dialog.exec()

    def _rebuild_mod(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = RebuildModDialog(self.factorio_plugin, self)
        dialog.exec()

    def _open_factorio_manager(self) -> None:
        if not self._require_factorio_plugin():
            return
        dialog = FactorioManagerDialog(
            self.factorio_plugin, self.plugin_system, game_id="factorio", parent=self
        )
        dialog.exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            translate("about.title"),
            translate("about.text"),
        )

    def closeEvent(self, event) -> None:  # noqa: N802
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
