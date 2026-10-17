"""Ejecuta makeself vía subprocess con logging y sin exponer secretos."""
from __future__ import annotations

import logging
import subprocess

from core.builder import build_argv
from core.model import MakeselfProject
from core.validator import validate

log = logging.getLogger("makeself_gui.runner")


def create(project: MakeselfProject, makeself_bin: str = "makeself") -> subprocess.CompletedProcess:
    errors = validate(project)
    if errors:
        raise ValueError("; ".join(errors))
    argv = build_argv(project, makeself_bin)
    log.info("makeself argv: %s", " ".join(argv[:3]) + " …")
    return subprocess.run(argv, capture_output=True, text=True, timeout=1200)
