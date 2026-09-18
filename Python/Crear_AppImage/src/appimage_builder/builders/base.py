"""Clase base para los builders de payload (Fase 3)."""

from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from pathlib import Path

from appimage_builder.core.exceptions import (
    BuildError,
    CancellationError,
    DependencyError,
)
from appimage_builder.core.models import BuildConfig, BuildProgress, ProjectConfig

ProgressCb = Callable[[BuildProgress], Awaitable[None]] | None


class BaseBuilder(ABC):
    """Instala el payload de la app dentro del AppDir.

    Cada builder recibe la configuración y la raíz del proyecto fuente, y
    debe dejar el/los ejecutables en `<appdir>/usr/bin/`.
    """

    stage = "installing_deps"

    def __init__(
        self,
        project: ProjectConfig,
        build: BuildConfig,
        project_root: Path,
    ) -> None:
        self.project = project
        self.build = build
        self.project_root = project_root

    @abstractmethod
    async def install(
        self,
        *,
        appdir: Path,
        progress: ProgressCb = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path | None:
        """Instala el payload. Devuelve el binario principal o None."""
        raise NotImplementedError

    async def report(
        self, progress: ProgressCb, frac: float, message: str, details: str = ""
    ) -> None:
        if progress is not None:
            await progress(
                BuildProgress(stage=self.stage, progress=frac, message=message, details=details)
            )

    def check_cancel(self, cancel_event: asyncio.Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise CancellationError()

    @staticmethod
    def require_tool(name: str, *, install_hint: str = "") -> str:
        path = shutil.which(name)
        if path is None:
            raise DependencyError(
                f"Herramienta requerida no encontrada: {name}",
                dependency=name,
                install_hint=install_hint or f"Instala {name} e intenta de nuevo.",
            )
        return path

    def binary_name(self) -> str:
        """Nombre del binario principal en `usr/bin`."""
        return self.project.entry_point or self.project.name

    def dest_binary(self, appdir: Path, name: str | None = None) -> Path:
        return appdir / "usr/bin" / (name or self.binary_name())

    def fail(
        self, message: str, *, command: str = "", output: str = "", hint: str = ""
    ) -> BuildError:
        return BuildError(
            message,
            stage=self.stage,
            command=command or None,
            output=output[-4000:] or None,
            hint=hint or None,
        )
