"""Plantilla de mod vacío para Factorio.

Contiene la estructura mínima de un mod de Factorio lista para ser
personalizada por Mod_Maker.
"""

from __future__ import annotations

from pathlib import Path

INFO_JSON_TEMPLATE = """{
  "name": "{{mod_name}}",
  "version": "1.0.0",
  "author": "{{author}}",
  "description": "{{description}}",
  "factorio_version": "{{factorio_version}}",
  "dependencies": ["base"],
  "homepage": ""
}
"""

DATA_LUA_TEMPLATE = """-- data.lua para {{mod_name}}
-- Generado por Mod_Maker

-- Agrega aquí tus prototipos de items, entidades, recetas y tecnologías
-- Ejemplo:
-- data:extend{
--     {
--         type = "item",
--         name = "{{mod_name}}-item",
--         icon = "__{{mod_name}}__/graphics/icon.png",
--         icon_size = 64,
--         stack_size = 100,
--     }
-- }
"""

DATA_FINAL_FIXES_TEMPLATE = """-- data-final-fixes.lua para {{mod_name}}
-- Generado por Mod_Maker
-- Ajustes finales que se aplican después de todos los demás mods
"""

PROTOTYPES_DIR_README = """# Prototypes

Aquí van los archivos de prototipos generados:
- items.lua
- recipes.lua
- technologies.lua
- entities.lua
"""

GRAPHICS_DIR_README = """# Graphics

Aquí van los gráficos del mod:
- icon.png
- spritesheets/
"""


def create_mod_template(
    target_dir: Path,
    mod_name: str,
    author: str = "",
    description: str = "",
    factorio_version: str = "2.0",
) -> None:
    """Crea la estructura de directorios y archivos de un mod vacío en target_dir."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # info.json
    info_content = INFO_JSON_TEMPLATE.replace("{{mod_name}}", mod_name)
    info_content = info_content.replace("{{author}}", author)
    info_content = info_content.replace("{{description}}", description)
    info_content = info_content.replace("{{factorio_version}}", factorio_version)
    (target_dir / "info.json").write_text(info_content, encoding="utf-8")

    # data.lua
    data_content = DATA_LUA_TEMPLATE.replace("{{mod_name}}", mod_name)
    (target_dir / "data.lua").write_text(data_content, encoding="utf-8")

    # data-final-fixes.lua
    fixes_content = DATA_FINAL_FIXES_TEMPLATE.replace("{{mod_name}}", mod_name)
    (target_dir / "data-final-fixes.lua").write_text(fixes_content, encoding="utf-8")

    # Carpetas
    (target_dir / "prototypes").mkdir(exist_ok=True)
    (target_dir / "graphics").mkdir(exist_ok=True)
    (target_dir / "locale").mkdir(exist_ok=True)

    # READMEs
    (target_dir / "prototypes" / "README.md").write_text(
        PROTOTYPES_DIR_README, encoding="utf-8"
    )
    (target_dir / "graphics" / "README.md").write_text(
        GRAPHICS_DIR_README, encoding="utf-8"
    )
