"""Diálogo para crear un item de Factorio sin código.

Formulario basado en Langbergio/Factorio-Mod-Creator-Studio:
permite definir nombre, stack size, subgrupo, grupo, icono y lugar
de creación sin escribir Lua manualmente.

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger

logger = get_logger(__name__)

# Subgrupos típicos de Factorio
SUBGROUPS = [
    "intermediate-product",
    "raw-resource",
    "transport-belt",
    "science-pack",
    "ammo",
    "armor",
    "capsule",
    "gun",
    "module",
    "rail-planner",
    "repair-tool",
    "selection-tool",
    "upgrade-item",
    "blueprint",
    "deconstruction-item",
    "item-with-label",
    "item-with-entity-info",
    "mining-tool",
    "fluid",
    "empty-barrel",
    "full-barrel",
    "burner-fuel",
    "combat-tool",
]

GRUPS = [
    "intermediate-products",
    "logistics",
    "production",
    "science",
    "combat",
    "fluid",
    "items-with-entities",
    "blueprint",
    "repair-tool",
    "selection-tool",
    "upgrade-item",
    "capsule",
    "ammunition",
    "armor",
    "module",
    "rail",
    "rail-planner",
    "mining-tool",
    "fluid",
    "combat-tool",
]


class NewItemDialog(QWidget):
    """Diálogo para crear un item de Factorio sin código."""

    def __init__(self, mod_name: str = "MyMod", parent=None) -> None:
        super().__init__(parent)
        self.mod_name = mod_name
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ej. mi-item-personalizado")
        form.addRow("Nombre interno:", self.name_edit)

        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("ej. Mi Item Personalizado")
        form.addRow("Nombre mostrado:", self.display_name_edit)

        self.stack_size_spin = QSpinBox()
        self.stack_size_spin.setRange(1, 100000)
        self.stack_size_spin.setValue(100)
        form.addRow("Tamaño de pila:", self.stack_size_spin)

        self.group_combo = QComboBox()
        self.group_combo.addItems(GRUPS)
        self.group_combo.setCurrentText("intermediate-products")
        form.addRow("Grupo:", self.group_combo)

        self.subgroup_combo = QComboBox()
        self.subgroup_combo.addItems(SUBGROUPS)
        self.subgroup_combo.setCurrentText("intermediate-product")
        form.addRow("Subgrupo:", self.subgroup_combo)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("icon.png")
        icon_btn = QPushButton("Seleccionar icono...")
        icon_btn.clicked.connect(self._select_icon)
        icon_row = QHBoxLayout()
        icon_row.setContentsMargins(0, 0, 0, 0)
        icon_row.setSpacing(5)
        icon_row.addWidget(self.icon_edit)
        icon_row.addWidget(icon_btn)
        form.addRow("Icono:", icon_row)

        self.place_result_edit = QLineEdit()
        self.place_result_edit.setPlaceholderText("ej. mi-entidad")
        form.addRow("Lugar de creación:", self.place_result_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.create_btn = QPushButton(translate("factorio.create_prototype"))
        self.create_btn.clicked.connect(self._accept)
        self.create_btn.setEnabled(False)
        btn_layout.addWidget(self.create_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.name_edit.textChanged.connect(self._validate_name)

    def _validate_name(self) -> None:
        name = self.name_edit.text().strip()
        self.create_btn.setEnabled(bool(name))

    def _select_icon(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar icono",
            "",
            "Imágenes (*.png *.jpg *.jpeg)",
        )
        if file_path:
            self.icon_edit.setText(file_path)

    def _accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                translate("factorio.create_prototype"),
                "El nombre del item es obligatorio.",
            )
            return

        import json

        item_data = {
            "name": name,
            "display_name": self.display_name_edit.text().strip() or name,
            "stack_size": self.stack_size_spin.value(),
            "group": self.group_combo.currentText(),
            "subgroup": self.subgroup_combo.currentText(),
            "icon": self.icon_edit.text().strip(),
            "place_result": self.place_result_edit.text().strip(),
        }

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar item como JSON",
            f"{name}.json",
            "Archivos JSON (*.json)",
        )
        if not output_path:
            return

        output_path = Path(output_path)
        try:
            with output_path.open("w", encoding="utf-8") as f:
                import json
                json.dump(item_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                translate("factorio.create_prototype"),
                f"Item '{name}' guardado en:\n{output_path}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error guardando item: %s", exc)
            QMessageBox.critical(
                self,
                translate("factorio.create_prototype"),
                f"Error guardando item: {exc}",
            )
