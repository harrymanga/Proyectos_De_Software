"""Exportador de mods de Factorio a archivo ZIP.

Empaqueta un mod en un archivo `.zip` siguiendo la estructura
esperada por Factorio (`mods/<name>_<version>.zip`).

Utiliza la función unificada mod_packager.build_mod_zip() para el
empaquetado real, evitando duplicación con FactorioPlugin.build().

Inspirado en:
- Langbergio/Factorio-Mod-Creator-Studio (export ZIP con un clic)
- justarandomgeek/factoriomod-debug (packaging and publishing)
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src.core.factorio_mod import FactorioMod
from src.core.mod_packager import build_mod_zip

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)


class FactorioExporter:
    """Empaqueta un mod de Factorio en un archivo .zip."""

    def __init__(self, mod: FactorioMod) -> None:
        self.mod = mod

    def export_zip(
        self,
        output_path: Path,
        include_source: bool = True,
    ) -> Path:
        """Empaqueta el mod en un archivo .zip.

        Estructura del ZIP:
        - info.json
        - data.lua
        - data-final-fixes.lua (opcional)
        - prototypes/ (opcional)
        - graphics/ (opcional)

        Devuelve la ruta del archivo ZIP creado.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determinar nombre del ZIP
        zip_name = f"{self.mod.metadata.name}_{self.mod.metadata.version}.zip"
        final_path = output_path / zip_name if output_path.is_dir() else output_path

        temp_dir = Path("/tmp") / f"modmaker_export_{self.mod.metadata.name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Guardar archivos del mod en directorio temporal
            self.mod.save_info_json(temp_dir)
            self.mod.save_data_lua(temp_dir)
            self.mod.save_data_final_fixes(temp_dir)

            # Empaquetar usando la función unificada
            return build_mod_zip(temp_dir, final_path)

        finally:
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir, ignore_errors=True)

    def export_from_directory(
        self,
        source_dir: Path,
        output_path: Path,
    ) -> Path:
        """Empaqueta un directorio existente como mod .zip.

        Usa la función unificada mod_packager.build_mod_zip().
        """
        return build_mod_zip(source_dir, output_path, self.mod.metadata.name, self.mod.metadata.version)
