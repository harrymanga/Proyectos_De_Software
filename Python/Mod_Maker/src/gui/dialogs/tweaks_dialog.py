"""Diálogo de ajustes (tweaks) para Factorio.

Genera data-final-fixes.lua desde sliders visuales,
inspirado en Supercraft Factorio Mod Generator.

Permite ajustar sin código:
- Velocidad de crafting
- Coste de recetas
- Tamaño de pilas de inventario

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import translate
from src.core.logger import get_logger
from src.core.tweak_generator import TweakGenerator

logger = get_logger(__name__)


class TweaksDialog(QWidget):
    """Diálogo de ajustes visuales para Factorio."""

    def __init__(self, mod_name: str = "MyMod", parent=None) -> None:
        super().__init__(parent)
        self.mod_name = mod_name
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        intro = QLabel(
            "Ajusta los valores de juego sin escribir código. "
            "Se generará un archivo data-final-fixes.lua."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(intro)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.crafting_spin = QDoubleSpinBox()
        self.crafting_spin.setRange(0.1, 100.0)
        self.crafting_spin.setValue(1.0)
        self.crafting_spin.setSingleStep(0.1)
        self.crafting_spin.setDecimals(2)
        form.addRow("Multiplicador de velocidad de crafting:", self.crafting_spin)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.1, 100.0)
        self.cost_spin.setValue(1.0)
        self.cost_spin.setSingleStep(0.1)
        self.cost_spin.setDecimals(2)
        form.addRow("Multiplicador de coste de recetas:", self.cost_spin)

        self.stack_spin = QSpinBox()
        self.stack_spin.setRange(0, 10000)
        self.stack_spin.setValue(0)
        form.addRow("Bonus de tamaño de pila:", self.stack_spin)

        self.mining_spin = QDoubleSpinBox()
        self.mining_spin.setRange(0.1, 100.0)
        self.mining_spin.setValue(1.0)
        self.mining_spin.setSingleStep(0.1)
        self.mining_spin.setDecimals(2)
        form.addRow("Multiplicador de velocidad de minería:", self.mining_spin)

        self.health_spin = QSpinBox()
        self.health_spin.setRange(0, 100000)
        self.health_spin.setValue(0)
        self.health_spin.setSpecialValueText("Sin cambios")
        form.addRow("Salud máxima del jugador:", self.health_spin)

        layout.addLayout(form)

        self.preview_label = QLabel("Preview: se generará al generar")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.preview_label)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.generate_btn = QPushButton(translate("factorio.generate_tweaks"))
        self.generate_btn.clicked.connect(self._generate_tweaks)
        btn_layout.addWidget(self.generate_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _generate_tweaks(self) -> None:
        generator = TweakGenerator(mod_name=self.mod_name)
        generator.set_crafting_speed(self.crafting_spin.value())
        generator.set_recipe_cost(self.cost_spin.value())
        generator.set_stack_size_bonus(self.stack_spin.value())
        generator.set_mining_speed(self.mining_spin.value())
        health = self.health_spin.value()
        generator.set_player_health(health if health > 0 else None)

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar data-final-fixes.lua",
            "data-final-fixes.lua",
            "Archivos Lua (*.lua)",
        )
        if not output_path:
            return

        output_path = Path(output_path)
        try:
            saved = generator.save_to_file(Path(output_path).parent)
            QMessageBox.information(
                self,
                translate("factorio.tweaks"),
                f"Archivo generado en:\n{saved}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            QMessageBox.critical(
                self,
                translate("factorio.tweaks"),
                f"Error generando archivo: {exc}",
            )
