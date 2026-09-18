"""Ejecutores de linuxdeploy / appimagetool / firma GPG."""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path

from appimage_builder.core.exceptions import (
    BuildError,
    CancellationError,
    DependencyError,
    SigningError,
)
from appimage_builder.core.models import BuildConfig, BuildProgress, ProjectConfig

ProgressCb = Callable[[BuildProgress], Awaitable[None]] | None


async def _report(
    progress: ProgressCb, stage: str, frac: float, message: str, details: str = ""
) -> None:
    if progress is not None:
        await progress(BuildProgress(stage=stage, progress=frac, message=message, details=details))


async def stream_command(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path,
    progress: ProgressCb = None,
    stage: str,
    message: str,
    cancel_event: asyncio.Event | None = None,
) -> str:
    """Ejecuta un comando con salida en streaming (reutilizable por builders)."""
    import os as _os

    return await _stream_process(
        cmd,
        env=env if env is not None else dict(_os.environ),
        cwd=cwd,
        progress=progress,
        stage=stage,
        message=message,
        cancel_event=cancel_event,
    )


async def _stream_process(
    cmd: list[str],
    *,
    env: dict[str, str],
    cwd: Path,
    progress: ProgressCb,
    stage: str,
    message: str,
    cancel_event: asyncio.Event | None = None,
) -> str:
    """Ejecuta un proceso capturando salida y reportando progreso indeterminado."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(cwd),
            env=env,
        )
    except FileNotFoundError as e:
        raise BuildError(
            f"Ejecutable no encontrado: {cmd[0]}",
            stage=stage,
            command=" ".join(cmd),
            hint="Ejecuta primero la descarga de runtimes.",
        ) from e

    output_lines: list[str] = []
    assert proc.stdout is not None
    while True:
        if cancel_event is not None and cancel_event.is_set():
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            raise CancellationError()
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode(errors="replace").rstrip()
        output_lines.append(text)
        if len(output_lines) > 200:
            output_lines.pop(0)
        await _report(progress, stage, 0.5, message, details=text[-200:])

    returncode = await proc.wait()
    output = "\n".join(output_lines)
    if returncode != 0:
        raise BuildError(
            f"Falló {' '.join(cmd[:2])}... (exit {returncode})",
            stage=stage,
            command=" ".join(cmd),
            output=output[-4000:],
        )
    return output


def _base_env(*, no_fuse: bool, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    if no_fuse:
        # Las AppImages-herramienta no pueden montarse sin FUSE: se auto-extraen.
        env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    if extra:
        env.update(extra)
    return env


def _ensure_tool(path: Path, name: str) -> Path:
    if not path.exists():
        raise DependencyError(
            f"{name} no encontrado en {path}",
            dependency=name,
            install_hint="Ejecuta el build con conexión a internet para descargarlo.",
        )
    return path


async def run_linuxdeploy(
    *,
    linuxdeploy: Path,
    appdir: Path,
    desktop_file: Path,
    icon_file: Path | None,
    apprun_file: Path,
    project: ProjectConfig,
    build: BuildConfig,
    no_fuse: bool = False,
    progress: ProgressCb = None,
    cancel_event: asyncio.Event | None = None,
) -> str:
    """Ejecuta linuxdeploy para poblar el AppDir con dependencias.

    Sin plugin de salida: solo despliega (desktop, icono, AppRun y
    dependencias del sistema) y deja la creación del AppImage a appimagetool.
    """
    import shutil as _shutil

    _ensure_tool(linuxdeploy, "linuxdeploy")
    # --custom-apprun no puede apuntar dentro del propio AppDir (linuxdeploy
    # intentaría copiar el archivo sobre sí mismo): usar una copia externa.
    external_apprun = apprun_file.parent.parent / "CustomAppRun"
    _shutil.copy2(apprun_file, external_apprun)
    external_apprun.chmod(0o755)
    cmd = [
        str(linuxdeploy),
        "--appdir",
        str(appdir),
        "--desktop-file",
        str(desktop_file),
        "--custom-apprun",
        str(external_apprun),
    ]
    if icon_file is not None and icon_file.exists():
        cmd.extend(["--icon-file", str(icon_file)])
    for excluded in build.excluded_libraries:
        cmd.extend(["--exclude-library", excluded])
    env = _base_env(no_fuse=no_fuse)
    return await _stream_process(
        cmd,
        env=env,
        cwd=appdir.parent,
        progress=progress,
        stage="running_linuxdeploy",
        message="Ejecutando linuxdeploy...",
        cancel_event=cancel_event,
    )


async def run_appimagetool(
    *,
    appimagetool: Path,
    appdir: Path,
    output: Path,
    project: ProjectConfig,
    build: BuildConfig,
    no_fuse: bool = False,
    progress: ProgressCb = None,
    cancel_event: asyncio.Event | None = None,
) -> Path:
    """Convierte el AppDir en AppImage. Devuelve la ruta del artefacto."""
    _ensure_tool(appimagetool, "appimagetool")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(appimagetool)]
    # Flags antes de los posicionales (appimagetool es estricto con el orden).
    comp_flag = {
        "xz": "xz",
        "gzip": "gzip",
        "zstd": "zstd",
        "lzo": "lzo",
    }.get(build.compression.value)
    if comp_flag:
        cmd.extend(["--comp", comp_flag])
    cmd.extend([str(appdir), str(output)])
    extra = {"ARCH": build.architecture.value}
    if build.update_information:
        extra["UPDATE_INFORMATION"] = build.update_information
    if build.sign:
        extra["SIGN"] = "1"
        if build.sign_key:
            extra["SIGN_KEY"] = build.sign_key
    env = _base_env(no_fuse=no_fuse, extra=extra)
    await _stream_process(
        cmd,
        env=env,
        cwd=appdir.parent,
        progress=progress,
        stage="creating_appimage",
        message="Creando AppImage con appimagetool...",
        cancel_event=cancel_event,
    )
    if not output.exists():
        # Algunas versiones anteponen VERSION al nombre; buscar candidato.
        candidates = sorted(output.parent.glob(f"{project.name}*.AppImage"))
        if candidates:
            return candidates[0]
        raise BuildError(
            f"appimagetool no generó {output}",
            stage="creating_appimage",
            command=" ".join(cmd),
            hint="Revisa la salida de appimagetool en modo --verbose.",
        )
    return output


async def sign_appimage(
    *,
    appimage: Path,
    sign_key: str | None,
    progress: ProgressCb = None,
) -> Path:
    """Firma el AppImage con GPG (`<app>.sig`)."""
    gpg = shutil.which("gpg")
    if gpg is None:
        raise SigningError(
            "GPG no encontrado para firmar.",
            key_id=sign_key,
            hint="Instala gnupg (ej: sudo pacman -S gnupg).",
        )
    sig = appimage.with_name(appimage.name + ".sig")
    cmd = [gpg, "--detach-sign", "--armor"]
    if sign_key:
        cmd.extend(["--local-user", sign_key])
    cmd.extend(["--output", str(sig), str(appimage)])
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        raise SigningError(
            f"Firma GPG falló (exit {proc.returncode}).",
            key_id=sign_key,
            hint="Verifica que la clave exista: gpg --list-secret-keys.",
        )
    await _report(progress, "signing", 1.0, "AppImage firmado", details=str(sig))
    _ = out
    return sig
