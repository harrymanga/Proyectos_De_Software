"""Validador de metainfo AppStream (`*.metainfo.xml` / `*.appdata.xml`)."""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from appimage_builder.core.models import ValidationResult

_REQUIRED_TAGS = ("id", "name", "summary", "description", "project_license", "launchable")


def validate_metainfo_file(path: Path, result: ValidationResult | None = None) -> ValidationResult:
    """Valida un XML de metainfo AppStream."""
    result = result or ValidationResult(valid=True)
    if not path.exists():
        return result.add_error(f"Metainfo no existe: {path}.")
    if not path.is_file():
        return result.add_error(f"No es un archivo: {path}.")

    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as e:
        return result.add_error(f"{path.name}: XML inválido ({e}).")

    if root.tag != "component":
        result = result.add_error(f"{path.name}: raíz <{root.tag}>, se esperaba <component>.")
    elif root.get("type") != "desktop-application":
        result = result.add_warning(
            f"{path.name}: type='{root.get('type')}', se esperaba 'desktop-application'."
        )

    children = {child.tag for child in root}
    for tag in _REQUIRED_TAGS:
        if tag not in children:
            result = result.add_error(f"{path.name}: falta el tag <{tag}>.")
    if root.tag == "component" and all(t in children for t in _REQUIRED_TAGS):
        result = result.add_info(f"Metainfo válido: {path.name}.")

    comp_id = root.findtext("id", default="").strip()
    if comp_id and not comp_id.endswith(".desktop"):
        result = result.add_warning(f"{path.name}: <id> debería terminar en '.desktop'.")

    return _external_check(path, result)


def _external_check(path: Path, result: ValidationResult) -> ValidationResult:
    """`appstreamcli validate` si existe (avisos como warnings)."""
    tool = shutil.which("appstreamcli")
    if tool is None:
        return result.add_info("appstreamcli no instalado (chequeo omitido).")
    try:
        proc = subprocess.run(
            [tool, "validate", "--no-net", str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return result.add_warning(f"appstreamcli no ejecutable: {e}.")
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0 and output:
        for line in output.splitlines()[:5]:
            line = line.strip()
            if line:
                result = result.add_warning(f"appstreamcli: {line}.")
    elif proc.returncode == 0:
        result = result.add_info("appstreamcli: sin hallazgos.")
    return result
