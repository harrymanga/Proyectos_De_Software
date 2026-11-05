"""Generador de sprite sheets para mods de Factorio.

Empaqueta imágenes individuales en hojas de sprites (sprite sheets) y genera
las entradas de `graphics` en los prototipos, inspirado en
Langbergio/Factorio-Mod-Creator-Studio.

Requiere Pillow (PIL) para manipulación de imágenes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover - dependencia opcional
    PIL_AVAILABLE = False

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)


class SpriteSheetGenerator:
    """Genera hojas de sprites a partir de imágenes individuales."""

    def __init__(self, mod_name: str = "MyMod") -> None:
        self.mod_name = mod_name
        self.sprites: list[dict[str, Any]] = []
        self.sheet_width: int = 256
        self.sheet_height: int = 256
        self.padding: int = 2

    def add_sprite(
        self,
        name: str,
        image_path: Path,
        width: int = 32,
        height: int = 32,
    ) -> None:
        """Agrega un sprite a la hoja."""
        self.sprites.append(
            {
                "name": name,
                "image_path": image_path,
                "width": width,
                "height": height,
            }
        )

    def generate_sheet(self, output_path: Path) -> dict[str, Any]:
        """Genera el archivo PNG de la hoja de sprites y devuelve metadatos.

        Devuelve un diccionario con:
        - sheet_path: ruta del PNG generado
        - sprites: lista de sprites con sus coordenadas en la hoja
        """
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow (PIL) es necesario para generar sprite sheets. "
                "Instálalo con: pip install Pillow"
            )

        if not self.sprites:
            raise ValueError("No hay sprites para empaquetar")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Crear hoja vacía
        sheet = Image.new("RGBA", (self.sheet_width, self.sheet_height), (0, 0, 0, 0))

        sprite_infos: list[dict[str, Any]] = []
        x = self.padding
        y = self.padding
        row_height = 0

        for sprite in self.sprites:
            img = Image.open(sprite["image_path"]).convert("RGBA")
            img = img.resize((sprite["width"], sprite["height"]), Image.LANCZOS)

            # Si no cabe en la fila, pasar a la siguiente
            if x + sprite["width"] + self.padding > self.sheet_width:
                x = self.padding
                y += row_height + self.padding
                row_height = 0

            # Si no cabe en la hoja, error
            if y + sprite["height"] + self.padding > self.sheet_height:
                raise ValueError(
                    f"La hoja de sprites es demasiado pequeña para "
                    f"el sprite '{sprite['name']}'"
                )

            sheet.paste(img, (x, y))
            sprite_infos.append(
                {
                    "name": sprite["name"],
                    "x": x,
                    "y": y,
                    "width": sprite["width"],
                    "height": sprite["height"],
                    "filename": f"{sprite['name']}.png",
                }
            )

            x += sprite["width"] + self.padding
            row_height = max(row_height, sprite["height"])

        sheet.save(output_path, "PNG")

        return {
            "sheet_path": str(output_path),
            "sheet_width": self.sheet_width,
            "sheet_height": self.sheet_height,
            "sprites": sprite_infos,
        }

    def generate_graphics_lua(self, sprite_infos: list[dict[str, Any]]) -> str:
        """Genera código Lua para las entradas de `graphics` de los prototipos."""
        lines: list[str] = []
        lines.append("-- Graphics generadas por Mod_Maker Sprite Sheet Generator")
        lines.append("")

        for info in sprite_infos:
            lines.append(f"-- {info['name']}")
            lines.append(f"data.raw.item[\"{info['name']}\"].icon = ")
            lines.append(
                f'    "__MOD_NAME__/graphics/spritesheets/{info["filename"]}",'
            )
            lines.append(
                f'data.raw.item["{info["name"]}"].icon_size = '
                f'{{{info["width"]}, {info["height"]}}},'
            )
            lines.append("")

        return "\n".join(lines)

    def save_sprite_metadata(self, output_dir: Path, metadata: dict[str, Any]) -> None:
        """Guarda metadatos del sprite sheet en JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        meta_path = output_dir / "sprite_sheet_meta.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
