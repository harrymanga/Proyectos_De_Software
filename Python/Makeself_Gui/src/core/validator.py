"""Validaciones previas a invocar makeself. core/validator.py"""
from __future__ import annotations

import os

from .model import MakeselfProject


def validate(project: MakeselfProject) -> list[str]:
    errors: list[str] = []
    if not project.archive_dir or not os.path.isdir(project.archive_dir):
        errors.append("archive_dir no existe o no es directorio")
    if not project.file_name:
        errors.append("file_name vacío")
    else:
        parent = os.path.dirname(os.path.abspath(project.file_name))
        if not os.path.isdir(parent):
            errors.append(f"directorio destino no existe: {parent}")
    if not project.label:
        errors.append("label vacío")
    # startup_script es opcional con --notemp/--current/--target, obligatorio si no
    needs_startup = not (
        project.options.notemp or project.options.current or project.options.target
    )
    if project.startup_script:
        full = os.path.join(project.archive_dir, project.startup_script.lstrip("./"))
        if not os.path.isfile(full) and not os.path.isfile(project.startup_script):
            errors.append(f"startup_script no encontrado: {project.startup_script}")
    elif needs_startup:
        errors.append("startup_script requerido (o usa --notemp/--current/--target)")
    if not 1 <= project.options.complevel <= 9:
        errors.append("complevel debe estar entre 1 y 9")
    if project.options.gpg_encrypt and project.options.ssl_encrypt:
        errors.append("gpg-encrypt y ssl-encrypt son excluyentes")
    return errors
