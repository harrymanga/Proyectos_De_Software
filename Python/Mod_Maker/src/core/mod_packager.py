"""Empaquetado de mods de Factorio a archivo ZIP.

Función unificada para reconstruir/exportar mods. Reemplaza la duplicación
que existía entre FactorioPlugin.build() y FactorioExporter.

Norma §3 (DRY): una sola función de empaquetado para todos los flujos.
Norma §25 (seguridad): valida info.json, previene path traversal,
bloquea extensiones peligrosas.

IMPORTANTE: Los mods de Factorio DEBEN empaquetarse con una carpeta
contenedora que contenga el nombre del mod (ej. MiMod_1.0.0/info.json).
Factorio no acepta mods con info.json en la raíz del ZIP.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from src.core.security import SecurityError, is_dangerous_extension

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

INFO_JSON = "info.json"
REQUIRED_METADATA_FIELDS = ("name", "version")


def build_mod_zip(
    source_dir: Path,
    output_path: Path,
    mod_name: str | None = None,
    mod_version: str | None = None,
) -> Path:
    """Empaqueta una carpeta como un mod .zip de Factorio.

    Esta es la función única de empaquetado. Tanto "Reconstruir mod"
    como "Exportar ZIP con un clic" la utilizan.

    El empaquetado SIEMPRE coloca los archivos dentro de una carpeta
    con el nombre del mod (ej. MiMod_1.0.0/info.json), tal como
    Factorio lo requiere.

    Args:
        source_dir: Carpeta que contiene el mod (debe tener info.json).
        output_path: Ruta del archivo ZIP de salida.
        mod_name: Nombre del mod para nombrar el ZIP (si output_path es directorio).
        mod_version: Versión del mod para nombrar el ZIP.

    Returns:
        Ruta del archivo ZIP creado.

    Raises:
        SecurityError: Si falta info.json, es inválida, o hay extensiones peligrosas.
    """
    source_dir = Path(source_dir)
    output_path = Path(output_path)

    if not source_dir.is_dir():
        raise SecurityError(f"La carpeta de origen no existe: {source_dir}")

    # Validar que exista info.json en la carpeta origen
    info_path = source_dir / INFO_JSON
    if not info_path.exists():
        raise SecurityError(
            f"Falta el archivo {INFO_JSON} en {source_dir}. "
            "Un mod de Factorio requiere info.json en la carpeta raíz del mod."
        )

    # Validar que info.json tenga campos requeridos
    try:
        with info_path.open("r", encoding="utf-8") as f:
            metadata: dict[str, Any] = json.load(f)
        for field in REQUIRED_METADATA_FIELDS:
            if field not in metadata or not str(metadata[field]).strip():
                raise SecurityError(
                    f"info.json carece del campo obligatorio '{field}'."
                )
    except json.JSONDecodeError as exc:
        raise SecurityError(f"info.json no es un JSON válido: {exc}") from exc

    # Determinar nombre del archivo ZIP de salida
    mod_folder_name = mod_name or str(metadata.get("name", "mod"))
    version = mod_version or str(metadata.get("version", "1.0.0"))

    # Determinar ruta de salida
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.is_dir():
        final_path = output_path / f"{mod_folder_name}_{version}.zip"
    else:
        final_path = output_path

    # Empaquetar archivos: SIEMPRE envolver en una carpeta con el nombre del mod
    # Factorio espera que el ZIP contenga una carpeta con el nombre del mod
    # (ej. MiMod_1.0.0/info.json), no archivos sueltos en la raíz.
    with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                arcname = Path(mod_folder_name) / file_path.relative_to(source_dir)
                if is_dangerous_extension(file_path):
                    logger.warning(
                        "Saltando archivo potencialmente peligroso: %s", arcname
                    )
                    continue
                zip_ref.write(file_path, arcname)

    logger.info("Mod empaquetado: %s -> %s", source_dir, final_path)
    return final_path
