"""Diálogo para gestionar mods instalados de cualquier juego."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.plugin_system import PluginSystem
from src.gui.dialogs.edit_mod_dialog import EditModDialog
from src.gui.dialogs.game_path_dialog import GamePathDialog
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class FactorioManagerDialog(QDialog):
    """Diálogo para listar, instalar, desinstalar, editar y gestionar mods de un juego."""

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
        self.setWindowTitle(f"{translate('dialog.manager.title')} — {self.game_name}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self._setup_ui()
        self.refresh_mods()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

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

        self.refresh_btn = QPushButton(translate("dialog.manager.refresh"))
        self.refresh_btn.clicked.connect(self.refresh_mods)
        btn_layout.addWidget(self.refresh_btn)

        self.config_path_btn = QPushButton("Configurar ruta de mods...")
        self.config_path_btn.clicked.connect(self._configure_mods_path)
        btn_layout.addWidget(self.config_path_btn)

        self.install_btn = QPushButton("Instalar mod...")
        self.install_btn.clicked.connect(self._install_mod)
        btn_layout.addWidget(self.install_btn)

        self.edit_btn = QPushButton("Editar mod")
        self.edit_btn.clicked.connect(self._edit_mod)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)

        self.uninstall_btn = QPushButton(translate("dialog.manager.uninstall"))
        self.uninstall_btn.clicked.connect(self._uninstall_mod)
        self.uninstall_btn.setEnabled(False)
        btn_layout.addWidget(self.uninstall_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Selección
        self.mods_list.itemSelectionChanged.connect(self._on_selection_changed)

    def refresh_mods(self) -> None:
        """Refresca la lista de mods instalados."""
        self.mods_list.clear()

        # Verificar si hay carpeta de mods configurada (detección automática o manual)
        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            self.info_label.setText(
                f"No se detectó la carpeta de mods de {self.game_name}. "
                "Use 'Configurar ruta de mods' para establecerla manualmente."
            )
            self.config_path_btn.setVisible(True)
            return
        else:
            self.info_label.setText(f"Carpeta de mods: {mods_folder}")
            self.config_path_btn.setVisible(False)

        try:
            mods = self.plugin.list_installed_mods()
            if not mods:
                item = QListWidgetItem(translate("dialog.manager.no_mods"))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.mods_list.addItem(item)
                return
            for mod_path in mods:
                item = QListWidgetItem(mod_path.name)
                item.setData(Qt.ItemDataRole.UserRole, str(mod_path))
                self.mods_list.addItem(item)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error listando mods: %s", exc)
            QMessageBox.warning(
                self,
                self.windowTitle(),
                translate("dialog.manager.error_detect"),
            )

    def _configure_mods_path(self) -> None:
        """Abre el diálogo genérico para configurar la carpeta de mods manualmente."""
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
                        self.windowTitle(),
                        f"No se pudo configurar la ruta: {exc}",
                    )

    def _on_selection_changed(self) -> None:
        item = self.mods_list.currentItem()
        has_selection = (
            item is not None
            and item.text() != translate("dialog.manager.no_mods")
        )
        self.uninstall_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)

    def _install_mod(self) -> None:
        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            QMessageBox.warning(
                self,
                self.windowTitle(),
                translate("dialog.manager.error_detect"),
            )
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

        # Validar mod
        if not self.plugin.validate(mod_path):
            QMessageBox.warning(
                self,
                self.windowTitle(),
                translate("error.invalid_mod"),
            )
            return

        # Detectar conflictos
        conflicts = self.plugin.detect_conflicts(mod_path)
        for conflict in conflicts:
            if conflict["tipo"] == "duplicado":
                reply = QMessageBox.question(
                    self,
                    self.windowTitle(),
                    translate(
                        "dialog.manager.confirm_overwrite", name=mod_path.name
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                break

        try:
            self.plugin.install_mod(mod_path)
            self.refresh_mods()
            QMessageBox.information(
                self,
                self.windowTitle(),
                translate("status.mod_installed", name=mod_path.name),
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error instalando mod: %s", exc)
            QMessageBox.critical(
                self,
                self.windowTitle(),
                translate("dialog.manager.error_install", error=str(exc)),
            )

    def _edit_mod(self) -> None:
        """Abre el diálogo de edición directa del mod seleccionado."""
        item = self.mods_list.currentItem()
        if not item:
            return

        mod_name = item.text()
        if mod_name == translate("dialog.manager.no_mods"):
            return

        mods_folder = self.plugin_system.get_game_folder(self.game_id)
        if not mods_folder:
            QMessageBox.warning(
                self,
                self.windowTitle(),
                translate("dialog.manager.error_detect"),
            )
            return

        mod_path = Path(mods_folder) / mod_name

        if not self.plugin.validate(mod_path):
            QMessageBox.warning(
                self,
                self.windowTitle(),
                translate("error.invalid_mod"),
            )
            return

        dialog = EditModDialog(self.plugin, mod_path, self)
        dialog.exec()

    def _uninstall_mod(self) -> None:
        item = self.mods_list.currentItem()
        if not item:
            return

        mod_name = item.text()
        if mod_name == translate("dialog.manager.no_mods"):
            return

        reply = QMessageBox.question(
            self,
            self.windowTitle(),
            translate("dialog.manager.confirm_uninstall", name=mod_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.plugin.uninstall_mod(mod_name)
            self.refresh_mods()
            QMessageBox.information(
                self,
                self.windowTitle(),
                translate("status.mod_uninstalled", name=mod_name),
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error desinstalando mod: %s", exc)
            QMessageBox.critical(
                self,
                self.windowTitle(),
                translate("dialog.manager.error_uninstall", error=str(exc)),
            )
