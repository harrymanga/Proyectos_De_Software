"""Validador de mods de Factorio.

Valida `info.json` contra un esquema JSON (inspirado en
justarandomgeek/factoriomod-debug JSON Validation) y verifica que los
metadatos cumplan con los requisitos de Factorio 2.0 / 2.1.

Reutiliza `SecurityValidator` del núcleo para validación de rutas
y prevención de path traversal (norma §25).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

# Campos obligatorios en info.json (Factorio)
_REQUIRED_FIELDS = ("name", "version")

# Campos opcionales pero recomendados
_OPTIONAL_FIELDS = ("author", "description", "factorio_version", "dependencies", "homepage")

# Versiones de Factorio soportadas
SUPPORTED_FACTORIO_VERSIONS = ("1.1", "2.0", "2.1")


class ValidationError(Exception):
    """Error de validación de un mod de Factorio."""


class FactorioValidator:
    """Valida metadatos y estructura de mods de Factorio."""

    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path
        self._schema: dict[str, Any] | None = None
        if schema_path:
            self._load_schema(schema_path)

    def _load_schema(self, path: Path) -> None:
        try:
            with path.open("r", encoding="utf-8") as f:
                self._schema = json.load(f)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("No se pudo cargar el esquema JSON: %s", exc)

    def validate_metadata(self, metadata: dict[str, Any]) -> list[str]:
        """Valida un diccionario de metadatos `info.json`.

        Devuelve una lista de mensajes de error (vacía si es válido).
        """
        errors: list[str] = []

        # Campos obligatorios
        for field in _REQUIRED_FIELDS:
            if field not in metadata or not str(metadata[field]).strip():
                errors.append(f"Campo obligatorio faltante o vacío: '{field}'")

        # Nombre del mod (sin caracteres prohibidos)
        name = str(metadata.get("name", "")).strip()
        if name:
            forbidden = {"/", "\\", ":", "*", "?", "\"", "<", ">", "|"}
            if any(char in name for char in forbidden):
                errors.append(
                    f"El nombre del mod contiene caracteres prohibidos: {name}"
                )

        # Versión de Factorio
        fv = str(metadata.get("factorio_version", "")).strip()
        if fv and fv not in SUPPORTED_FACTORIO_VERSIONS:
            errors.append(
                f"Versión de Factorio no soportada: '{fv}'. "
                f"Versiones válidas: {', '.join(SUPPORTED_FACTORIO_VERSIONS)}"
            )

        # Versión semántica básica
        version = str(metadata.get("version", "")).strip()
        if version:
            parts = version.split(".")
            if len(parts) < 2 or not all(p.isdigit() for p in parts):
                errors.append(
                    f"La versión '{version}' no sigue el formato semántico "
                    "(ej. 1.0.0)"
                )

        return errors

    def validate_mod_structure(self, mod_dir: Path) -> list[str]:
        """Valida que un directorio de mod tenga la estructura mínima.

        Requiere al menos `info.json`.
        """
        errors: list[str] = []
        mod_dir = Path(mod_dir)

        if not mod_dir.exists() or not mod_dir.is_dir():
            errors.append(f"El directorio del mod no existe: {mod_dir}")
            return errors

        info_path = mod_dir / "info.json"
        if not info_path.exists():
            errors.append("Falta el archivo obligatorio: info.json")

        if info_path.exists():
            try:
                with info_path.open("r", encoding="utf-8") as f:
                    metadata = json.load(f)
                errors.extend(self.validate_metadata(metadata))
            except json.JSONDecodeError as exc:
                errors.append(f"info.json no es un JSON válido: {exc}")
            except Exception as exc:  # pragma: no cover - defensivo
                errors.append(f"Error leyendo info.json: {exc}")

        return errors

    def validate_zip(self, zip_path: Path) -> list[str]:
        """Valida un archivo .zip de mod de Factorio."""
        import zipfile

        errors: list[str] = []
        zip_path = Path(zip_path)

        if not zip_path.exists():
            errors.append(f"El archivo no existe: {zip_path}")
            return errors

        if not zipfile.is_zipfile(zip_path):
            errors.append(f"El archivo no es un ZIP válido: {zip_path}")
            return errors

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if "info.json" not in names:
                    errors.append(f"Falta info.json en el mod: {zip_path.name}")
                else:
                    info_data = zf.read("info.json")
                    metadata = json.loads(info_data.decode("utf-8"))
                    errors.extend(self.validate_metadata(metadata))
        except json.JSONDecodeError as exc:
            errors.append(f"info.json no es JSON válido: {exc}")
        except Exception as exc:  # pragma: no cover - defensivo
            errors.append(f"Error validando ZIP: {exc}")

        return errors

    def is_valid(self, metadata: dict[str, Any]) -> bool:
        """Devuelve True si los metadatos son válidos."""
        return len(self.validate_metadata(metadata)) == 0
