"""Generador de prototipos Lua para mods de Factorio.

Convierte definiciones de prototipos (items, tecnologías, recetas, entidades)
en código Lua válido para Factorio, siguiendo el estándar de:

- Langbergio/Factorio-Mod-Creator-Studio (prototipos sin código)
- Supercraft Factorio Mod Generator (data-final-fixes.lua)

Normas: §10 (arquitectura modular), §47 (anti-God Object).
"""

from __future__ import annotations

from typing import Any

from src.core.factorio_mod import PrototypeItem, PrototypeTechnology


class PrototypeGenerator:
    """Genera código Lua de prototipos de Factorio a partir de definiciones."""

    def __init__(self, mod_name: str = "MyMod") -> None:
        self.mod_name = mod_name
        self.items: list[PrototypeItem] = []
        self.technologies: list[PrototypeTechnology] = []
        self.recipes: list[dict] = []
        self.entities: list[dict] = []

    def add_item(
        self,
        name: str,
        stack_size: int = 100,
        subgroup: str = "intermediate-product",
        group: str = "intermediate-products",
        order: str = "a",
        icon: str | None = None,
        place_result: str | None = None,
    ) -> PrototypeItem:
        """Agrega un prototipo de item."""
        item = PrototypeItem(
            name=name,
            stack_size=stack_size,
            subgroup=subgroup,
            group=group,
            order=order,
            icon=icon,
            place_result=place_result,
        )
        self.items.append(item)
        return item

    def add_technology(
        self,
        name: str,
        enabled: bool = False,
        icon: str | None = None,
        effects: list[dict] | None = None,
        prerequisites: list[str] | None = None,
        unit_count: int = 100,
        unit_ingredients: list[list[Any]] | None = None,
        unit_time: int = 30,
    ) -> PrototypeTechnology:
        """Agrega un prototipo de tecnología."""
        tech = PrototypeTechnology(
            name=name,
            enabled=enabled,
            icon=icon,
            effects=effects or [],
            prerequisites=prerequisites or [],
            unit={
                "count": unit_count,
                "ingredients": unit_ingredients or [["automation-science-pack", 1]],
                "time": unit_time,
            },
        )
        self.technologies.append(tech)
        return tech

    def add_recipe(
        self,
        name: str,
        ingredients: list[list[Any]],
        results: list[list[Any]],
        energy_required: float = 0.5,
        enabled: bool = False,
    ) -> dict:
        """Agrega una receta."""
        recipe = {
            "type": "recipe",
            "name": name,
            "ingredients": ingredients,
            "results": results,
            "energy_required": energy_required,
            "enabled": enabled,
        }
        self.recipes.append(recipe)
        return recipe

    def generate_lua(self) -> str:
        """Genera todo el código Lua de prototipos."""
        blocks: list[str] = []

        # Items
        for item in self.items:
            blocks.append(item.to_lua())

        # Recetas
        for recipe in self.recipes:
            blocks.append(self._recipe_to_lua(recipe))

        # Tecnologías
        for tech in self.technologies:
            blocks.append(tech.to_lua())

        # Entidades
        for entity in self.entities:
            blocks.append(self._entity_to_lua(entity))

        return "\n\n".join(blocks)

    def _recipe_to_lua(self, recipe: dict) -> str:
        lines: list[str] = []
        lines.append(f"-- recipe: {recipe['name']}")
        lines.append("data:extend{")
        lines.append("    {")
        lines.append('        type = "recipe",')
        lines.append(f'        name = "{recipe["name"]}",')
        lines.append(f'        energy_required = {recipe["energy_required"]},')
        lines.append(f'        enabled = {str(recipe["enabled"]).lower()},')
        lines.append("        ingredients = {")
        for ing in recipe["ingredients"]:
            lines.append(f'            {{"{ing[0]}", {ing[1]}}},')
        lines.append("        },")
        lines.append("        results = {")
        for res in recipe["results"]:
            lines.append(f'            {{"{res[0]}", {res[1]}}},')
        lines.append("        },")
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)

    def _entity_to_lua(self, entity: dict) -> str:
        lines: list[str] = []
        lines.append(f"-- entity: {entity.get('name', '')}")
        lines.append("data:extend{")
        lines.append("    {")
        lines.append(f'        type = "{entity.get("type", "item")}",')
        lines.append(f'        name = "{entity.get("name", "")}",')
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)

    def replace_mod_name_placeholder(self, lua_content: str) -> str:
        """Reemplaza __MOD_NAME__ por el nombre real del mod."""
        return lua_content.replace("__MOD_NAME__", self.mod_name)
