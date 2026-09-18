"""Validador de archivos `.desktop` (Freedesktop)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from appimage_builder.core.models import ValidationResult

_REQUIRED_KEYS = ("Name=", "Exec=", "Icon=")
_DESKTOP_HEADER = "[Desktop Entry]"


def validate_desktop_file(path: Path, result: ValidationResult | None = None) -> ValidationResult:
    """Valida un `.desktop` concreto."""
    result = result or ValidationResult(valid=True)
    if not path.exists():
        return result.add_error(f".desktop no existe: {path}.")
    if not path.is_file():
        return result.add_error(f"No es un archivo: {path}.")

    try:
        content = path.read_text(errors="replace")
    except OSError as e:
        return result.add_error(f"No se pudo leer {path}: {e}.")

    if _DESKTOP_HEADER not in content:
        result = result.add_error(f"{path.name}: falta la cabecera {_DESKTOP_HEADER}.")
    if "Type=Application" not in content:
        result = result.add_error(f"{path.name}: falta 'Type=Application'.")
    for key in _REQUIRED_KEYS:
        if key not in content:
            result = result.add_warning(f"{path.name}: sin clave {key}.")

    exec_value = _entry_value(content, "Exec")
    if exec_value and ":" in exec_value:
        result = result.add_warning(
            f"{path.name}: Exec={exec_value!r} parece 'modulo:funcion'; "
            "se espera el binario lanzador."
        )
    categories = _entry_value(content, "Categories")
    if categories is not None and not categories.endswith(";"):
        result = result.add_warning(f"{path.name}: Categories debería terminar en ';'.")

    if not any(k in content for k in ("Name=", "Exec=", "Icon=")):
        return result
    result = result.add_info(f".desktop válido: {path.name}.")
    return _external_check(path, result)


def _entry_value(content: str, key: str) -> str | None:
    for line in content.splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return None


def _external_check(path: Path, result: ValidationResult) -> ValidationResult:
    """`desktop-file-validate` si existe (sus avisos son warnings, no errores)."""
    tool = shutil.which("desktop-file-validate")
    if tool is None:
        return result.add_info("desktop-file-validate no instalado (chequeo omitido).")
    try:
        proc = subprocess.run([tool, str(path)], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return result.add_warning(f"desktop-file-validate no ejecutable: {e}.")
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0 and output:
        for line in output.splitlines()[:5]:
            result = result.add_warning(f"desktop-file-validate: {line.strip()}.")
    elif proc.returncode == 0:
        result = result.add_info("desktop-file-validate: sin hallazgos.")
    return result
