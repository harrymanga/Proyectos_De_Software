"""Proyecto .msgui.json para recrear .run. core/project.py"""
from __future__ import annotations

import dataclasses
import json
import os
import shutil

from .model import MakeselfOptions, MakeselfProject


def save(project: MakeselfProject, path: str) -> None:
    data = dataclasses.asdict(project)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load(path: str) -> MakeselfProject:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    opts = MakeselfOptions(**data.pop("options", {}))
    return MakeselfProject(options=opts, **data)


def place_startup(archive_dir: str, script_path: str) -> tuple[str, bool]:
    """Deja el script inicial dentro de archive_dir (Makeself lo exige).

    Devuelve (ruta_relativa_para_makeself, copiado).
    Si script_path ya está dentro, solo lo relativiza. Si está fuera,
    lo copia a la raíz de archive_dir evitando sobrescribir.
    """
    script_path = script_path.strip()
    if not script_path:
        return "", False
    archive_abs = os.path.abspath(archive_dir)
    candidate = script_path
    # Ruta ya relativa al archive (./x o x)
    if not os.path.isabs(candidate):
        stripped = candidate[2:] if candidate.startswith("./") else candidate
        if os.path.isfile(os.path.join(archive_abs, stripped)):
            return "./" + stripped, False
        if os.path.isfile(candidate):
            candidate = os.path.abspath(candidate)
        else:
            return script_path, False
    candidate_abs = os.path.abspath(candidate)
    if os.path.commonpath([archive_abs, candidate_abs]) == archive_abs:
        rel = os.path.relpath(candidate_abs, archive_abs)
        return "./" + rel, False
    base = os.path.basename(candidate_abs)
    dest = os.path.join(archive_abs, base)
    if os.path.isfile(dest):
        with open(dest, "rb") as f1, open(candidate_abs, "rb") as f2:
            if f1.read() == f2.read():
                return "./" + base, False
        name, ext = os.path.splitext(base)
        index = 1
        while os.path.exists(dest):
            dest = os.path.join(archive_abs, f"{name}-{index}{ext}")
            index += 1
    shutil.copy2(candidate_abs, dest)
    try:
        os.chmod(dest, os.stat(dest).st_mode | 0o111)
    except OSError:
        pass
    return "./" + os.path.basename(dest), True


def from_info(info: dict, archive_dir: str = "", file_name: str = "") -> MakeselfProject:
    """Crea un proyecto reconstruido (aproximado) desde parse_info()."""
    script = info.get("script", "").strip()
    return MakeselfProject(
        archive_dir=archive_dir,
        file_name=file_name,
        label=info.get("identification", ""),
        startup_script=script if script and script != "none" else "",
        reconstructed=True,
    )
