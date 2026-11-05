"""Generador de tweaks para Factorio.

Genera `data-final-fixes.lua` a partir de valores de sliders y configuración
visual, inspirado en Supercraft Factorio Mod Generator.

Permite ajustar sin código:
- Velocidad de crafting
- Coste de recetas
- Tamaño de pilas de inventario
- Otros parámetros del juego
"""

from __future__ import annotations

from pathlib import Path


class TweakGenerator:
    """Genera código Lua de `data-final-fixes.lua` desde valores de tweaks."""

    def __init__(self, mod_name: str = "MyMod") -> None:
        self.mod_name = mod_name
        self.crafting_speed_multiplier: float = 1.0
        self.recipe_cost_multiplier: float = 1.0
        self.inventory_stack_size_bonus: int = 0
        self.mining_speed_multiplier: float = 1.0
        self.player_character_health: int | None = None

    def set_crafting_speed(self, multiplier: float) -> None:
        self.crafting_speed_multiplier = multiplier

    def set_recipe_cost(self, multiplier: float) -> None:
        self.recipe_cost_multiplier = multiplier

    def set_stack_size_bonus(self, bonus: int) -> None:
        self.inventory_stack_size_bonus = bonus

    def set_mining_speed(self, multiplier: float) -> None:
        self.mining_speed_multiplier = multiplier

    def set_player_health(self, health: int | None) -> None:
        self.player_character_health = health

    def generate_lua(self) -> str:
        """Genera el contenido completo de `data-final-fixes.lua`."""
        lines: list[str] = []
        lines.append(f"-- data-final-fixes.lua para {self.mod_name}")
        lines.append("-- Generado por Mod_Maker (Supercraft-style tweaks)")
        lines.append("")

        # Crafting speed
        if self.crafting_speed_multiplier != 1.0:
            lines.append("-- Ajustar velocidad de crafting")
            lines.append(
                "for _, recipe in pairs(data.raw.recipe) do"
            )
            lines.append(
                "    if recipe.energy_required then"
            )
            lines.append(
                f"        recipe.energy_required = recipe.energy_required / {self.crafting_speed_multiplier}"
            )
            lines.append("    end")
            lines.append("end")
            lines.append("")

        # Recipe cost
        if self.recipe_cost_multiplier != 1.0:
            lines.append("-- Ajustar coste de recetas")
            lines.append(
                "for _, recipe in pairs(data.raw.recipe) do"
            )
            lines.append(
                "    if recipe.ingredients then"
            )
            lines.append(
                "        for _, ingredient in pairs(recipe.ingredients) do"
            )
            lines.append(
                f"            ingredient[2] = ingredient[2] * {self.recipe_cost_multiplier}"
            )
            lines.append("        end")
            lines.append("    end")
            lines.append("end")
            lines.append("")

        # Stack size bonus
        if self.inventory_stack_size_bonus > 0:
            lines.append("-- Ajustar tamaños de pila de inventario")
            lines.append(
                "for _, item in pairs(data.raw.item) do"
            )
            lines.append(
                "    if item.stack_size then"
            )
            lines.append(
                f"        item.stack_size = item.stack_size + {self.inventory_stack_size_bonus}"
            )
            lines.append("    end")
            lines.append("end")
            lines.append("")

        # Mining speed
        if self.mining_speed_multiplier != 1.0:
            lines.append("-- Ajustar velocidad de minería")
            lines.append(
                "for _, entity in pairs(data.raw.entity) do"
            )
            lines.append(
                "    if entity.minable and entity.minable.mining_time then"
            )
            lines.append(
                f"        entity.minable.mining_time = entity.minable.mining_time / {self.mining_speed_multiplier}"
            )
            lines.append("    end")
            lines.append("end")
            lines.append("")

        # Player health
        if self.player_character_health is not None:
            lines.append("-- Ajustar salud del jugador")
            lines.append(
                "if data.raw['character']['character'] then"
            )
            lines.append(
                f"    data.raw['character']['character'].max_health = {self.player_character_health}"
            )
            lines.append("end")
            lines.append("")

        if not lines:
            lines.append("-- No hay tweaks aplicados")
            lines.append("")

        return "\n".join(lines)

    def save_to_file(self, target_dir: Path) -> Path:
        """Guarda `data-final-fixes.lua` en el directorio destino."""
        target_dir.mkdir(parents=True, exist_ok=True)
        fixes_path = target_dir / "data-final-fixes.lua"
        content = self.generate_lua()
        fixes_path.write_text(content, encoding="utf-8")
        return fixes_path
