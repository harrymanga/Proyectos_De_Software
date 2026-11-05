"""Diálogo para gestionar mods instalados de cualquier juego."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.plugin_system import PluginSystem
from src.gui.dialogs.edit_mod_dialog import EditModDialog
from src.gui.dialogs.game_path_dialog import GamePathDialog
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class FactorioManagerDialog(QWidget):
    """Diálogo para listar, instalar, desinstalar, editar y gestionar mods de un juego.

    Diseñado para ser embebido como pestaña en la ventana principal.
    """

    def __init__(
        self,
        plugin: FactorioPlugin,
        plugin_system: PluginSystem,
        game_id: str = "factorio",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.plugin_system = plugin_system
        self.game_id = game_id
        self.game_name = plugin.game_name
        self._setup_ui()
        self.refresh_mods()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Mensaje informativo sobre la carpeta de mods
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #ffaa00; font-style: italic;")
        layout.addWidget(self.info_label)

        # Lista de mods
        self.mods_list = QListWidget()
        self.mods_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.mods_list)

        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.refresh_btn = QPushButton(translate("dialog.manager.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_mods)
        btn_layout.addWidget(self.refresh_btn)

        self.config_path_btn = QPushButton(translate("dialog.create_mod.select_folder"))
        self.config_path_btn.clicked.connect(self._configure_mods_path)
        btn_layout.addWidget(self.config_path_btn)

        self.install_btn = QPushButton(translate("dialog.create_mod.create"))
        self.install_btn.clicked.connect(self._install_mod)
        btn_layout.addWidget(self.install_btn)

        self.edit_btn = QPushButton("Editar mod")
        self.edit_btn.clicked.connect(self._edit_mod)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)

        self.uninstall_btn = QPushButton("Desinstalar")
        self.uninstall_btn.clicked.connect(self._uninstall_mod)
        self.uninstall_btn.setEnabled(False)
        btn_layout.addWidget(self.uninstall_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Selección
        self.mods_list.itemSelectionChanged.connect(self._on_selection_changed)

    def refresh_mods(self) -> None:
        """Refresca la lista de mods instalados."""
        self.mods_list.clear()

        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            self.info_label.setText(
                f"No se detectó la carpeta de mods de {self.game_name}. "
                "Use 'Seleccionar carpeta de contenido' para establecerla manualmente."
            )
            self.config_path_btn.setVisible(True)
            return
        else:
            self.info_label.setText(f"Carpeta de mods: {mods_folder}")
            self.config_path_btn.setVisible(False)

        try:
            mods = self.plugin.list_installed_mods()
            if not mods:
                return
            for mod_path in mods:
                item = QListWidgetItem(mod_path.name)
                item.setData(Qt.ItemDataRole.UserRole, str(mod_path))
                self.mods_list.addItem(item)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error listando mods: %s", exc)

    def _configure_mods_path(self) -> None:
        """Abre el diálogo para configurar la carpeta de mods manualmente."""
        current = self.plugin_system.get_game_folder(self.game_id)
        dialog = GamePathDialog(self.game_name, current, self)
        if dialog.exec():
            new_path = dialog.get_selected_path()
            if new_path:
                try:
                    self.plugin_system.set_game_folder(self.game_id, new_path)
                    self.refresh_mods()
                except Exception as exc:  # pragma: no cover - defensivo
                    logger.error("Error configurando ruta: %s", exc)
                    QMessageBox.critical(
                        self,
                        translate("dialog.create_mod.title"),
                        f"No se pudo configurar la ruta: {exc}",
                    )

    def _on_selection_changed(self) -> None:
        item = self.mods_list.currentItem()
        has_selection = (
            item is not None
        )
        self.uninstall_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)

    def _install_mod(self) -> None:
        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar mod para instalar",
            "",
            "Archivos ZIP (*.zip)",
        )
        if not file_path:
            return

        mod_path = Path(file_path)

        if not self.plugin.validate(mod_path):
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_name_invalid"),
            )
            return

        try:
            self.plugin.install_mod(mod_path)
            self.refresh_mods()
            QMessageBox.information(
                self,
                translate("dialog.create_mod.title"),
                f"Mod instalado: {mod_path.name}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error instalando mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.create_mod.title"),
                f"Error instalando mod: {exc}",
            )

    def _edit_mod(self) -> None:
        """Abre el diálogo de edición directa del mod seleccionado."""
        item = self.mods_list.currentItem()
        if not item:
            return

        mod_name = item.text()
        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            return

        mod_path = Path(mods_folder) / mod_name

        if not self.plugin.validate(mod_path):
            QMessageBox.warning(
                self,
                translate("dialog.create_mod.title"),
                translate("dialog.create_mod.error_name_invalid"),
            )
            return


        dialog = EditModDialog(self.plugin, mod_path, self)
        dialog.exec()

    def _uninstall_mod(self) -> None:
        item = self.mods_list.currentItem()
        if not item:
            return

        mod_name = item.text()

        try:
            self.plugin.uninstall_mod(mod_name)
            self.refresh_mods()
            QMessageBox.information(
                self,
                translate("dialog.create_mod.title"),
                f"Mod desinstalado: {mod_name}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error desinstalando mod: %s", exc)
            QMessageBox.critical(
                self,
                translate("dialog.create_mod.title"),
                f"Error desinstalando mod: {exc}",
            )
