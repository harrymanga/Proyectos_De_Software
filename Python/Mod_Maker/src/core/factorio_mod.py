"""Modelo de datos de un mod de Factorio para Mod_Maker.

Implementa la estructura de metadatos `info.json` y el modelo de prototipos
(items, tecnologías, recetas, entidades) siguiendo el estándar de Factorio
(v2.0 / v2.1 / Space Age).

Referencias oficiales:
- https://wiki.factorio.com/Modding
- https://wiki.factorio.com/Tutorial:Modding_tutorial/Gangsir
- https://lua-api.factorio.com/latest/

Normas aplicadas: §10 (arquitectura modular), §13 (configuración separada),
§17 (manejo de errores), §25 (seguridad), §49 (regla maestra).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Expresión regular para nombres válidos de mods de Factorio:
# Solo letras minúsculas, números y guiones. Sin espacios.
MOD_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")

# Campos obligatorios en info.json según la documentación oficial
_REQUIRED_INFO_JSON_FIELDS = ("name", "version")

# Campos opcionales reconocidos en info.json
_OPTIONAL_INFO_JSON_FIELDS = (
    "title",
    "author",
    "description",
    "factorio_version",
    "dependencies",
    "homepage",
)

# Extensiones de archivo válidas para la carpeta de un mod
VALID_MOD_FILES = {
    "info.json",
    "data.lua",
    "data-updates.lua",
    "data-final-fixes.lua",
    "control.lua",
    "settings.lua",
    "settings-updates.lua",
    "settings-final-fixes.lua",
    "migrations.lua",
}


class ModValidationError(Exception):
    """Excepción lanzada cuando un mod no cumple con los estándares de Factorio."""


@dataclass
class ModMetadata:
    """Metadatos del mod (equivalente al archivo `info.json` de Factorio).

    Según la documentación oficial de Factorio:
    https://lua-api.factorio.com/latest/auxiliary/mod-structure.html#info.json
    """

    name: str
    version: str
    author: str = ""
    description: str = ""
    factorio_version: str = "2.0"
    dependencies: list[str] = field(default_factory=list)
    homepage: str = ""

    def validate(self) -> None:
        """Valida que los metadatos cumplan con los estándares de Factorio.

        Raises:
            ModValidationError: Si algún campo obligatorio falta o es inválido.
        """
        if not self.name or not self.name.strip():
            raise ModValidationError("El campo 'name' es obligatorio y no puede estar vacío.")

        # Validar nombre según las normas de Factorio:
        # - Solo letras minúsculas, números y guiones
        # - No puede empezar ni terminar con guion
        # - No puede tener espacios
        name = self.name.strip()
        if not MOD_NAME_PATTERN.match(name):
            raise ModValidationError(
                f"El nombre del mod '{name}' no es válido. "
                "Debe usar solo letras minúsculas, números y guiones, "
                "y no puede empezar ni terminar con guion."
            )

        if not self.version or not self.version.strip():
            raise ModValidationError("El campo 'version' es obligatorio y no puede estar vacío.")

        # Validar formato de versión (número.número.número)
        version = self.version.strip()
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            raise ModValidationError(
                f"La versión '{version}' no tiene un formato válido. "
                "Debe ser del formato 'número.número.número' (ej. 1.0.0)."
            )

        if not self.factorio_version or not self.factorio_version.strip():
            raise ModValidationError(
                "El campo 'factorio_version' es obligatorio y no puede estar vacío."
            )

    def to_dict(self) -> dict[str, Any]:
        """Devuelve el diccionario listo para serializar a JSON (info.json)."""
        return {
            "name": self.name.strip(),
            "version": self.version.strip(),
            "author": self.author.strip(),
            "description": self.description.strip(),
            "factorio_version": self.factorio_version.strip(),
            "dependencies": self.dependencies,
            "homepage": self.homepage.strip(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModMetadata:
        return cls(
            name=data.get("name", ""),
            version=data.get("version", ""),
            author=data.get("author", ""),
            description=data.get("description", ""),
            factorio_version=data.get("factorio_version", "2.0"),
            dependencies=data.get("dependencies", []),
            homepage=data.get("homepage", ""),
        )


@dataclass
class PrototypeItem:
    """Prototipo de un item de Factorio.

    Documentación: https://lua-api.factorio.com/latest/prototypes/ItemPrototype.html
    """

    name: str
    type: str = "item"
    stack_size: int = 100
    subgroup: str = "intermediate-product"
    group: str = "intermediate-products"
    order: str = "a"
    icon: str | None = None
    place_result: str | None = None
    flags: list[str] = field(default_factory=lambda: ["goes-to-main-inventory"])

    def validate_name(self) -> None:
        """Valida que el nombre del prototipo cumpla con las normas de Factorio."""
        if not MOD_NAME_PATTERN.match(self.name):
            raise ModValidationError(
                f"El nombre del prototipo '{self.name}' no es válido. "
                "Debe usar solo letras minúsculas, números y guiones."
            )

    def to_lua(self) -> str:
        """Genera el código Lua del prototipo."""
        self.validate_name()
        lines: list[str] = []
        lines.append(f"-- {self.type}: {self.name}")
        lines.append("data:extend{")
        lines.append("    {")
        lines.append(f'        type = "{self.type}",')
        lines.append(f'        name = "{self.name}",')
        if self.stack_size > 0:
            lines.append(f'        stack_size = {self.stack_size},')
        lines.append(f'        subgroup = "{self.subgroup}",')
        lines.append(f'        group = "{self.group}",')
        lines.append(f'        order = "{self.order}",')
        if self.icon:
            lines.append(f'        icon = "__MOD_NAME__/graphics/{self.icon}",')
        if self.place_result:
            lines.append(f'        place_result = "{self.place_result}",')
        if self.flags:
            flags_str = ", ".join(f'"{f}"' for f in self.flags)
            lines.append(f'        flags = {{{flags_str}}},')
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)


@dataclass
class PrototypeTechnology:
    """Prototipo de una tecnología de Factorio.

    Documentación: https://lua-api.factorio.com/latest/prototypes/TechnologyPrototype.html
    """

    name: str
    type: str = "technology"
    enabled: bool = False
    icon: str | None = None
    effects: list[dict[str, Any]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    unit: dict[str, Any] = field(default_factory=lambda: {
        "count": 100,
        "ingredients": [["automation-science-pack", 1]],
        "time": 30,
    })

    def validate_name(self) -> None:
        if not MOD_NAME_PATTERN.match(self.name):
            raise ModValidationError(
                f"El nombre de la tecnología '{self.name}' no es válido."
            )

    def to_lua(self) -> str:
        self.validate_name()
        lines: list[str] = []
        lines.append(f"-- {self.type}: {self.name}")
        lines.append("data:extend{")
        lines.append("    {")
        lines.append(f'        type = "{self.type}",')
        lines.append(f'        name = "{self.name}",')
        lines.append(f'        enabled = {str(self.enabled).lower()},')
        if self.icon:
            lines.append(f'        icon = "__MOD_NAME__/graphics/{self.icon}",')
        if self.prerequisites:
            preqs = ", ".join(f'"{p}"' for p in self.prerequisites)
            lines.append(f'        prerequisites = {{{preqs}}},')
        lines.append('        unit = {')
        lines.append(f'            count = {self.unit.get("count", 100)},')
        lines.append('            ingredients = {')
        for ing in self.unit.get("ingredients", []):
            lines.append(f'                {{"{ing[0]}", {ing[1]}}},')
        lines.append('            },')
        lines.append(f'            time = {self.unit.get("time", 30)},')
        lines.append('        },')
        if self.effects:
            lines.append('        effects = {')
            for eff in self.effects:
                lines.append('            {')
                lines.append(f'                type = "{eff.get("type", "unlock-recipe")}",')
                lines.append(f'                recipe = "{eff.get("recipe", "")}"')
                lines.append('            },')
            lines.append('        },')
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)


@dataclass
class FactorioMod:
    """Modelo completo de un mod de Factorio.

    Contiene metadatos (`info.json`) y una colección de prototipos
    que se pueden exportar a archivos Lua y empaquetar en un `.zip`.

    Estructura de carpetas esperada (según documentación oficial):
        <mod-name>/
            info.json          (obligatorio)
            data.lua           (opcional - prototipos)
            data-updates.lua   (opcional)
            data-final-fixes.lua (opcional)
            control.lua        (opcional - scripting en tiempo de ejecución)
            settings.lua       (opcional - configuración)
            locale/
                en/
                    any_name.cfg
    """

    metadata: ModMetadata
    items: list[PrototypeItem] = field(default_factory=list)
    technologies: list[PrototypeTechnology] = field(default_factory=list)
    recipes: list[dict[str, Any]] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    data_final_fixes: str = ""
    control_script: str = ""

    def validate(self) -> None:
        """Valida todo el mod antes de empaquetar."""
        self.metadata.validate()
        for item in self.items:
            item.validate_name()
        for tech in self.technologies:
            tech.validate_name()

    def to_info_json_dict(self) -> dict[str, Any]:
        """Devuelve el diccionario para `info.json`."""
        return self.metadata.to_dict()

    def to_lua_prototypes(self) -> str:
        """Genera todo el código Lua de los prototipos."""
        blocks: list[str] = []
        for item in self.items:
            blocks.append(item.to_lua())
        for tech in self.technologies:
            blocks.append(tech.to_lua())
        if self.data_final_fixes:
            blocks.append("-- data-final-fixes.lua")
            blocks.append(self.data_final_fixes)
        return "\n\n".join(blocks)

    def save_info_json(self, target_dir: Path) -> None:
        """Guarda `info.json` en el directorio destino."""
        target_dir.mkdir(parents=True, exist_ok=True)
        info_path = target_dir / "info.json"
        with info_path.open("w", encoding="utf-8") as f:
            json.dump(self.to_info_json_dict(), f, indent=2, ensure_ascii=False)

    def save_data_lua(self, target_dir: Path) -> None:
        """Guarda `data.lua` con los prototipos generados."""
        target_dir.mkdir(parents=True, exist_ok=True)
        data_path = target_dir / "data.lua"
        lua_content = self.to_lua_prototypes()
        with data_path.open("w", encoding="utf-8") as f:
            f.write(lua_content)

    def save_data_final_fixes(self, target_dir: Path) -> None:
        """Guarda `data-final-fixes.lua` si hay contenido."""
        if not self.data_final_fixes:
            return
        target_dir.mkdir(parents=True, exist_ok=True)
        fixes_path = target_dir / "data-final-fixes.lua"
        with fixes_path.open("w", encoding="utf-8") as f:
            f.write(self.data_final_fixes)

    def save_control_lua(self, target_dir: Path) -> None:
        """Guarda `control.lua` si hay contenido."""
        if not self.control_script:
            return
        target_dir.mkdir(parents=True, exist_ok=True)
        control_path = target_dir / "control.lua"
        with control_path.open("w", encoding="utf-8") as f:
            f.write(self.control_script)
