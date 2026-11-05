"""Explorador de mods integrado para el panel lateral izquierdo.

Muestra la lista de juegos con mods detectados y los mods instalados
de cada uno, permitiendo seleccionar un mod para editarlo o gestionarlo.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import get_logger
from src.core.plugin_system import PluginSystem

logger = get_logger(__name__)


class ModsExplorerPanel(QWidget):
    """Panel lateral izquierdo: lista de juegos y mods instalados.

    Emite mod_selected cuando el usuario selecciona un mod para editarlo.
    """

    mod_selected = Signal(str)  # ruta del archivo .zip del mod

    def __init__(
        self,
        plugin_system: PluginSystem,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin_system = plugin_system
        self._setup_ui()
        self.refresh_mods()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Mods instalados")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        # Lista de mods
        self.mods_list = QListWidget()
        self.mods_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.mods_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.mods_list)

        # Botón refrescar
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_mods)
        layout.addWidget(self.refresh_btn)

        # Botón editar mod seleccionado
        self.edit_btn = QPushButton("Editar mod seleccionado")
        self.edit_btn.clicked.connect(self._edit_selected)
        self.edit_btn.setEnabled(False)
        layout.addWidget(self.edit_btn)

        # Selección
        self.mods_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        item = self.mods_list.currentItem()
        has_selection = (
            item is not None
            and item.text() != "No hay mods instalados en Factorio."
        )
        self.edit_btn.setEnabled(has_selection)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        text = item.text()
        if text == "No hay mods instalados en Factorio.":
            return
        mod_path = item.data(Qt.ItemDataRole.UserRole)
        if mod_path:
            self.mod_selected.emit(mod_path)

    def _edit_selected(self) -> None:
        item = self.mods_list.currentItem()
        if not item:
            return
        mod_path = item.data(Qt.ItemDataRole.UserRole)
        if mod_path:
            self.mod_selected.emit(mod_path)

    def refresh_mods(self) -> None:
        """Refresca la lista de mods instalados."""
        self.mods_list.clear()
        mods_folder = self.plugin_system.get_game_folder("factorio")
        if not mods_folder:
            item = QListWidgetItem(
                "No se detectó la carpeta de mods de Factorio."
            )
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.mods_list.addItem(item)
            return
        try:
            mods = self.plugin_system.get_plugin("factorio").list_installed_mods()
            if not mods:
                item = QListWidgetItem(
                    "No hay mods instalados en Factorio."
                )
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.mods_list.addItem(item)
                return
            for mod_path in mods:
                item = QListWidgetItem(mod_path.name)
                item.setData(Qt.ItemDataRole.UserRole, str(mod_path))
                self.mods_list.addItem(item)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error listando mods: %s", exc)
            item = QListWidgetItem(f"Error al listar mods: {exc}")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.mods_list.addItem(item)
