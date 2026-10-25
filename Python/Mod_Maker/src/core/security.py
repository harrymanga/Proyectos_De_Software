"""Validación de seguridad para extracción y reconstrucción de mods.

Norma §25: validación de entradas, prevención de path traversal,
bloqueo de ejecución de código arbitrario.
"""

from __future__ import annotations

import os
from pathlib import Path

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

# Extensiones consideradas peligrosas si se extraen sin validación
DANGEROUS_EXTENSIONS = {".exe", ".dll", ".so", ".dylib", ".bat", ".sh", ".ps1", ".cmd"}


class SecurityError(Exception):
    """Error de seguridad al validar rutas o archivos de mods."""


def is_path_within(base_dir: Path, target_path: Path) -> bool:
    """Devuelve True si target_path está dentro de base_dir (evita path traversal)."""
    try:
        base_resolved = base_dir.resolve()
        target_resolved = target_path.resolve()
        return str(target_resolved).startswith(str(base_resolved) + os.sep) or (
            target_resolved == base_resolved
        )
    except Exception as exc:  # pragma: no cover - defensivo
        logger.error("Error validando ruta: %s", exc)
        return False


def validate_extraction_target(dest_dir: Path, member_path: str) -> Path:
    """Valida que un miembro de archivo comprimido no salga de dest_dir.

    Devuelve la ruta segura dentro de dest_dir o lanza SecurityError.
    """
    dest_resolved = dest_dir.resolve()
    candidate = (dest_resolved / member_path).resolve()
    if not is_path_within(dest_resolved, candidate):
        raise SecurityError(
            f"Path traversal detectado: {member_path} intentaba escribir fuera de {dest_dir}"
        )
    return candidate


def is_dangerous_extension(file_path: Path) -> bool:
    """Devuelve True si el archivo tiene una extensión considerada peligrosa."""
    return file_path.suffix.lower() in DANGEROUS_EXTENSIONS


def validate_mod_name(name: str) -> None:
    """Valida que el nombre de un mod sea seguro para usar como carpeta/archivo."""
    if not name or not name.strip():
        raise SecurityError("El nombre del mod no puede estar vacío")
    forbidden = {"/", "\\", ":", "*", "?", "\"", "<", ">", "|"}
    if any(char in name for char in forbidden):
        raise SecurityError(
            f"El nombre del mod contiene caracteres prohibidos: {', '.join(sorted(forbidden))}"
        )
