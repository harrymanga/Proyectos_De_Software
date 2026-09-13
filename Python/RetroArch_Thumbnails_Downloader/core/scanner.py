"""Compat: re-exporta desde core.systems (no leer JSON en cada llamada)."""
from core.systems import (
    detect_system,
    expand_systems,
    list_extensions,
    list_system_names,
    load_systems_raw as load_systems,
    validate_system_extension,
)

__all__ = [
    "load_systems",
    "expand_systems",
    "detect_system",
    "validate_system_extension",
    "list_extensions",
    "list_system_names",
]
