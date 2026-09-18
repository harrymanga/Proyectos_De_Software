"""Validador de estructura AppDir (usa los validadores desktop/appstream)."""

from __future__ import annotations

from pathlib import Path

from appimage_builder.core.models import ValidationResult
from appimage_builder.validators.appstream import validate_metainfo_file
from appimage_builder.validators.desktop import validate_desktop_file


def validate_appdir(appdir: Path, result: ValidationResult | None = None) -> ValidationResult:
    """Aplica las reglas mínimas del estándar AppDir."""
    result = result or ValidationResult(valid=True)
    if not appdir.exists():
        return result.add_error(f"AppDir no existe: {appdir}.")
    if not appdir.is_dir():
        return result.add_error(f"No es un directorio: {appdir}.")

    apprun = appdir / "AppRun"
    if not apprun.exists():
        result = result.add_error("Falta AppRun en la raíz del AppDir.")
    elif not apprun.stat().st_mode & 0o111:
        result = result.add_error("AppRun no es ejecutable (chmod +x).")
    else:
        result = result.add_info("AppRun presente y ejecutable.")

    desktops = sorted(appdir.glob("*.desktop"))
    if not desktops:
        result = result.add_error("Falta archivo .desktop en la raíz del AppDir.")
    else:
        result = result.add_info(f".desktop encontrado: {desktops[0].name}.")
        result = validate_desktop_file(desktops[0], result)

    icons = sorted(appdir.glob("*.png")) + sorted(appdir.glob("*.svg"))
    if not icons:
        result = result.add_warning("Sin icono en la raíz del AppDir (*.png/*.svg).")
    else:
        result = result.add_info(f"Icono encontrado: {icons[0].name}.")

    if not (appdir / "usr/bin").is_dir():
        result = result.add_warning("Falta usr/bin dentro del AppDir.")

    metainfo = (
        sorted((appdir / "usr/share/metainfo").glob("*.xml"))
        if (appdir / "usr/share/metainfo").is_dir()
        else []
    )
    if not metainfo:
        result = result.add_warning("Sin metainfo en usr/share/metainfo (*.xml).")
    else:
        result = result.add_info(f"Metainfo encontrado: {metainfo[0].name}.")
        result = validate_metainfo_file(metainfo[0], result)

    return result
