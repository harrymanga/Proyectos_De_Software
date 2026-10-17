"""Chequeo previo de espacio: makeself usa ~2x el tamaño en temporales."""
from __future__ import annotations

import os
import re
import shutil

_MARGIN = 512 * 1024 * 1024


def dir_size(path: str) -> int:
    total = 0
    for _dir, _subdirs, files in os.walk(path, followlinks=False):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(_dir, name))
            except OSError:
                continue
    return total


def fmt_size(num: int) -> str:
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def check_space(archive_dir: str, file_name: str, tmpdir: str = "") -> list[str]:
    """Advierte si falta espacio en temporales o destino. Vacío = OK."""
    warnings: list[str] = []
    try:
        src = dir_size(archive_dir)
    except OSError:
        return warnings
    tmp = tmpdir or os.environ.get("TMPDIR", "/tmp")
    dest_parent = os.path.dirname(os.path.abspath(file_name)) or "/tmp"
    needs = [(tmp, src * 2 + _MARGIN), (dest_parent, src + _MARGIN)]
    for folder, need in needs:
        try:
            free = shutil.disk_usage(folder).free
        except OSError:
            warnings.append(f"no se puede medir espacio en {folder}")
            continue
        if free < need:
            warnings.append(
                f"poco espacio en {folder}: libre {fmt_size(free)}, "
                f"necesario ~{fmt_size(need)}"
            )
    return warnings


_ABOUT_TO_COMPRESS = re.compile(r"About to compress (\d+) KB")


def uncompressed_kb(build_output: str) -> int | None:
    """Extrae los KB sin comprimir del log de makeself, o None."""
    match = _ABOUT_TO_COMPRESS.search(build_output or "")
    return int(match.group(1)) if match else None
