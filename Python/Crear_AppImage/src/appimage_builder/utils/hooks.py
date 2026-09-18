"""Ejecución compartida de hooks de shell (pre-package / post-install)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from appimage_builder.core.exceptions import BuildError


def run_hook_script(
    hook: Path,
    *,
    name: str,
    stage: str,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> str:
    """Ejecuta un script bash como hook. Devuelve su stdout.

    Raises:
        BuildError: si el hook no existe o falla (con salida recortada).
    """
    hook_path = hook.expanduser()
    if not hook_path.exists():
        raise BuildError(
            f"Hook {name} no encontrado: {hook_path}",
            stage=stage,
            hint="Verifica la ruta del hook en la configuración.",
        )
    env = dict(os.environ, **(extra_env or {}))
    try:
        proc = subprocess.run(
            ["bash", str(hook_path)],
            cwd=str(cwd),
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise BuildError(
            f"Hook {name} falló (exit {e.returncode}): {(e.stderr or '').strip()}",
            stage=stage,
            command=str(hook_path),
            output=((e.stdout or "") + (e.stderr or ""))[-4000:],
        ) from e
    return proc.stdout
