"""Gestor de runtimes: linuxdeploy + appimagetool (descarga, cache, permisos)."""

from __future__ import annotations

import os
import stat
from collections.abc import Awaitable, Callable
from pathlib import Path

from appimage_builder.core.constants import (
    APPIMAGETOOL_RELEASE_URL,
    LINUXDEPLOY_RELEASE_URL,
    Architecture,
)
from appimage_builder.core.exceptions import RuntimeError as ToolRuntimeError
from appimage_builder.core.models import BuildProgress, RuntimeConfig
from appimage_builder.runtime.downloader import download_file

ProgressCb = Callable[[BuildProgress], Awaitable[None]] | None

_TOOLS_DIRNAME = "tools"


class RuntimeManager:
    """Resuelve y cachea las herramientas externas de build.

    Orden de resolución por herramienta:

    1. Ruta local explícita (`linuxdeploy_path` / `appimagetool_path`):
       se usa tal cual (tras `chmod +x`), sin red.
    2. Cache (`<cache_dir>/tools/linuxdeploy-<arch>.AppImage`, idem
       appimagetool).
    3. Descarga desde GitHub continuous.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        architecture: Architecture = Architecture.X86_64,
    ) -> None:
        self.config = config
        self.architecture = architecture

    @property
    def tools_dir(self) -> Path:
        d = self.config.cache_dir.expanduser().resolve() / _TOOLS_DIRNAME
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def linuxdeploy_path(self) -> Path:
        return self.tools_dir / f"linuxdeploy-{self.architecture.value}.AppImage"

    @property
    def appimagetool_path(self) -> Path:
        return self.tools_dir / f"appimagetool-{self.architecture.value}.AppImage"

    def linuxdeploy_url(self) -> str:
        return LINUXDEPLOY_RELEASE_URL.format(arch=self.architecture.value)

    def appimagetool_url(self) -> str:
        return APPIMAGETOOL_RELEASE_URL.format(arch=self.architecture.value)

    def is_available(self) -> bool:
        """True si ambas herramientas están listas (local, cache o ambas)."""
        return self.is_linuxdeploy_available() and self.is_appimagetool_available()

    def resolve_linuxdeploy(self) -> Path:
        """Ruta efectiva: local explícita o cache (sin validar existencia)."""
        local = self._local_tool(self.config.linuxdeploy_path, tool="linuxdeploy")
        return local if local is not None else self.linuxdeploy_path

    def resolve_appimagetool(self) -> Path:
        """Ruta efectiva: local explícita o cache (sin validar existencia)."""
        local = self._local_tool(self.config.appimagetool_path, tool="appimagetool")
        return local if local is not None else self.appimagetool_path

    def _local_tool(self, configured: Path | None, *, tool: str) -> Path | None:
        """Valida una ruta local explícita (la hace ejecutable si hace falta)."""
        if configured is None:
            return None
        path = configured.expanduser()
        if not path.exists():
            raise ToolRuntimeError(
                f"Ruta local de {tool} no existe: {path}.",
                tool=tool,
                hint="Verifica runtime.linuxdeploy_path/appimagetool_path.",
            )
        if not path.is_file():
            raise ToolRuntimeError(f"Ruta local de {tool} no es un archivo: {path}.", tool=tool)
        if not self._is_executable(path):
            try:
                self._make_executable(path)
            except OSError as e:
                raise ToolRuntimeError(
                    f"No se pudo hacer ejecutable {tool}: {path}.", tool=tool
                ) from e
        return path

    async def _report_ready(self, progress: ProgressCb, tool: str, path: Path, origin: str) -> None:
        if progress is not None:
            await progress(
                BuildProgress(
                    stage="downloading_runtime",
                    progress=1.0,
                    message=f"{tool} listo ({origin})",
                    details=str(path),
                )
            )

    def is_linuxdeploy_available(self) -> bool:
        return self._is_executable(self.resolve_linuxdeploy())

    def is_appimagetool_available(self) -> bool:
        return self._is_executable(self.resolve_appimagetool())

    @staticmethod
    def _is_executable(path: Path) -> bool:
        return path.exists() and bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP))

    def _auth_headers(self) -> dict[str, str]:
        token = self.config.github_token or os.environ.get("GITHUB_TOKEN")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    @staticmethod
    def _make_executable(path: Path) -> None:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    async def ensure_all(self, progress: ProgressCb = None) -> dict[str, Path]:
        """Garantiza ambas herramientas; devuelve sus rutas."""
        linuxdeploy = await self.ensure_linuxdeploy(progress)
        appimagetool = await self.ensure_appimagetool(progress)
        return {"linuxdeploy": linuxdeploy, "appimagetool": appimagetool}

    async def ensure_linuxdeploy(self, progress: ProgressCb = None) -> Path:
        local = self._local_tool(self.config.linuxdeploy_path, tool="linuxdeploy")
        if local is not None:
            await self._report_ready(progress, "linuxdeploy", local, "local")
            return local
        if self._is_executable(self.linuxdeploy_path):
            await self._report_ready(progress, "linuxdeploy", self.linuxdeploy_path, "cache")
            return self.linuxdeploy_path
        return await self._fetch(
            tool="linuxdeploy",
            url=self.linuxdeploy_url(),
            dest=self.linuxdeploy_path,
            progress=progress,
            base=0.0,
            span=0.5,
        )

    async def ensure_appimagetool(self, progress: ProgressCb = None) -> Path:
        local = self._local_tool(self.config.appimagetool_path, tool="appimagetool")
        if local is not None:
            await self._report_ready(progress, "appimagetool", local, "local")
            return local
        if self._is_executable(self.appimagetool_path):
            await self._report_ready(progress, "appimagetool", self.appimagetool_path, "cache")
            return self.appimagetool_path
        return await self._fetch(
            tool="appimagetool",
            url=self.appimagetool_url(),
            dest=self.appimagetool_path,
            progress=progress,
            base=0.5,
            span=0.5,
        )

    async def _fetch(
        self,
        *,
        tool: str,
        url: str,
        dest: Path,
        progress: ProgressCb,
        base: float,
        span: float,
    ) -> Path:
        async def on_bytes(downloaded: int, total: int | None) -> None:
            if progress is None:
                return
            frac = (downloaded / total) if total else 0.0
            frac = max(0.0, min(1.0, frac))
            await progress(
                BuildProgress(
                    stage="downloading_runtime",
                    progress=base + span * frac,
                    message=f"Descargando {tool} ({downloaded // 1024} KiB)...",
                    details=url,
                )
            )

        try:
            await download_file(url, dest, headers=self._auth_headers(), progress=on_bytes)
        except Exception as e:
            raise ToolRuntimeError(
                f"No se pudo obtener {tool}",
                tool=tool,
                hint="Verifica conexión a internet, GITHUB_TOKEN y permisos en cache.",
            ) from e
        self._make_executable(dest)
        if progress is not None:
            await progress(
                BuildProgress(
                    stage="downloading_runtime",
                    progress=base + span,
                    message=f"{tool} listo",
                    details=str(dest),
                )
            )
        return dest

    def clear_cache(self) -> None:
        """Elimina las herramientas cacheadas."""
        for path in (self.linuxdeploy_path, self.appimagetool_path):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass
