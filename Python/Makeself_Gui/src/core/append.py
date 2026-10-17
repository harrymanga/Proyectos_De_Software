"""Añade archivos a un .run existente vía `makeself --append`."""
from __future__ import annotations

import logging
import os
import subprocess

log = logging.getLogger("makeself_gui.append")


def append_to_archive(
    extra_dir: str, run_path: str, makeself_bin: str = "makeself"
) -> subprocess.CompletedProcess:
    if not os.path.isdir(extra_dir):
        raise ValueError(f"extra_dir no existe: {extra_dir}")
    if not os.path.isfile(run_path):
        raise ValueError(f".run no existe: {run_path}")
    argv = [makeself_bin, "--append", extra_dir, run_path]
    log.info("append: %s + %s", extra_dir, run_path)
    return subprocess.run(argv, capture_output=True, text=True, timeout=1200)
