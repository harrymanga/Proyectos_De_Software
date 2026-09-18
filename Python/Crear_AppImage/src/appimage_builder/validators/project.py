"""Validador de la configuración del core (semántica, no sintaxis)."""

from __future__ import annotations

from appimage_builder.core.models import AppImageBuilderConfig, ValidationResult


def validate_project_config(
    config: AppImageBuilderConfig, result: ValidationResult | None = None
) -> ValidationResult:
    """Chequeos semánticos sobre una config ya parseada."""
    result = result or ValidationResult(valid=True)
    result = result.add_info(
        f"Config OK: {config.project.name} {config.project.version} "
        f"({config.project.build_type.value})"
    )
    if not config.project.entry_point and config.project.build_type.value != "generic":
        result = result.add_warning("entry_point vacío para un proyecto no genérico.")
    if config.project.icon is not None and not config.project.icon.exists():
        result = result.add_warning(f"Icono no encontrado: {config.project.icon}.")
    for extra in config.build.extra_files:
        if not extra.exists():
            result = result.add_warning(f"Archivo extra no encontrado: {extra}.")
    if config.build.sign and not config.build.sign_key:
        result = result.add_info("Firma sin Key ID: se usará la clave GPG por defecto.")
    return result
