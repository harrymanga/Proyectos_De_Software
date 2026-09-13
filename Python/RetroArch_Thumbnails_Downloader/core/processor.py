"""Lógica pura de procesamiento (testeable, sin Qt)."""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from core.downloader import download
from core.matcher import normalize
from core.systems import detect_system, list_extensions, validate_system_extension

Status = Literal["ok", "unknown_system", "invalid_name", "bad_extension", "not_found"]


@dataclass(frozen=True)
class ProcessResult:
    file: str
    status: Status
    system: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    message: str = ""


def build_thumbnail_url(system: str, art_type: str, name: str) -> str:
    return f"https://thumbnails.libretro.com/{system}/{art_type}/{name}.png"


def resolve_file(file: str, art_type: str, selected_system: Optional[str] = None) -> ProcessResult:
    if selected_system:
        if not validate_system_extension(file, selected_system):
            return ProcessResult(file, "bad_extension", selected_system, message="bad_extension")
        system = selected_system
    else:
        system = detect_system(file) or ""
        if not system:
            return ProcessResult(file, "unknown_system", message="unknown_system")
    name = normalize(file)
    if not name:
        return ProcessResult(file, "invalid_name", system, message="invalid_name")
    return ProcessResult(file, "ok", system, name, build_thumbnail_url(system, art_type, name))


def process_file(
    file: str, art_type: str = "Named_Boxarts", selected_system: Optional[str] = None
) -> ProcessResult:
    resolved = resolve_file(file, art_type, selected_system)
    if resolved.status != "ok" or not resolved.url:
        return resolved
    result = download(resolved.url)
    if result:
        return ProcessResult(resolved.file, "ok", resolved.system, resolved.name, resolved.url, "OK")
    return ProcessResult(resolved.file, "not_found", resolved.system, resolved.name, resolved.url, "not_found")


def find_rom_files(directory: str | Path, recursive: bool = True) -> list[str]:
    root = Path(str(directory))
    if not root.is_dir():
        return []
    exts = {e.lower() for e in list_extensions()}
    pattern = "**/*" if recursive else "*"
    files = []
    for p in root.glob(pattern):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(str(p))
    return sorted(files)


def rename_rom_for_thumbnail(file_path: str, thumbnail_name: str) -> str:
    directory = Path(str(file_path)).parent
    ext = Path(str(file_path)).suffix
    decoded = urllib.parse.unquote(thumbnail_name)
    # Evitar path traversal desde el nombre del thumbnail
    safe = Path(decoded).name
    new_path = directory / f"{safe}{ext}"
    counter = 1
    stem = new_path.stem
    while new_path.exists():
        new_path = directory / f"{stem}_{counter}{ext}"
        counter += 1
    Path(str(file_path)).rename(new_path)
    return str(new_path)
