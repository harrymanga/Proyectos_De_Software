"""Diálogo de sprite sheet para Factorio.

Genera hojas de sprites a partir de imágenes individuales,
inspirado en Langbergio/Factorio-Mod-Creator-Studio.

Requiere Pillow (PIL).

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
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
from src.core.sprite_sheet_generator import SpriteSheetGenerator

logger = get_logger(__name__)


class SpriteSheetDialog(QWidget):
    """Diálogo para generar sprite sheets de Factorio."""

    def __init__(self, mod_name: str = "MyMod", parent=None) -> None:
        super().__init__(parent)
        self.mod_name = mod_name
        self._image_files: list[Path] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        intro = QLabel(
            "Selecciona imágenes PNG para empaquetar en una hoja de sprites. "
            "Se generarán las entradas de graphics en Lua."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.files_label = QLabel("0 imágenes seleccionadas")
        layout.addWidget(self.files_label)

        btn_images = QPushButton("Seleccionar imágenes...")
        btn_images.clicked.connect(self._select_images)
        layout.addWidget(btn_images)

        # Configuración
        form = QHBoxLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(64, 2048)
        self.width_spin.setValue(256)
        form.addWidget(QLabel("Ancho de hoja:"))
        form.addWidget(self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(64, 2048)
        self.height_spin.setValue(256)
        form.addWidget(QLabel("Alto de hoja:"))
        form.addWidget(self.height_spin)

        layout.addLayout(form)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.generate_btn = QPushButton(translate("factorio.generate_sheet"))
        self.generate_btn.clicked.connect(self._generate_sheet)
        btn_layout.addWidget(self.generate_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _select_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar imágenes para sprite sheet",
            "",
            "Imágenes (*.png *.jpg *.jpeg)",
        )
        if files:
            self._image_files = [Path(f) for f in files]
            self.files_label.setText(f"{len(self._image_files)} imagen(es) seleccionada(s)")

    def _generate_sheet(self) -> None:
        if not self._image_files:
            QMessageBox.warning(
                self,
                translate("factorio.sprite_sheet"),
                "Debe seleccionar al menos una imagen.",
            )
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino para sprite sheet"
        )
        if not output_dir:
            return

        output_dir = Path(output_dir)

        try:
            generator = SpriteSheetGenerator(mod_name=self.mod_name)
            generator.sheet_width = self.width_spin.value()
            generator.sheet_height = self.height_spin.value()

            for i, img_path in enumerate(self._image_files):
                generator.add_sprite(
                    name=f"sprite_{i}",
                    image_path=img_path,
                    width=32,
                    height=32,
                )

            sheet_path = generator.generate_sheet(output_dir / "spritesheet.png")
            generator.save_sprite_metadata(
                output_dir,
                sheet_path,
            )

            lua_graphics = generator.generate_graphics_lua(sheet_path["sprites"])
            lua_path = output_dir / "graphics.lua"
            lua_path.write_text(lua_graphics, encoding="utf-8")

            QMessageBox.information(
                self,
                translate("factorio.sprite_sheet"),
                f"Sprite sheet generada en:\n{sheet_path['sheet_path']}\n\n"
                f"Código Lua en:\n{lua_path}",
            )

        except ImportError as exc:
            QMessageBox.critical(
                self,
                translate("factorio.sprite_sheet"),
                f"Error: {exc}",
            )
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error generando sprite sheet: %s", exc)
            QMessageBox.critical(
                self,
                translate("factorio.sprite_sheet"),
                f"Error generando sprite sheet: {exc}",
            )
