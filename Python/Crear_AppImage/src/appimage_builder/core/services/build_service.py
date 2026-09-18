"""Servicio de build principal - Orquestación del pipeline."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from appimage_builder.bundler.appdir import AppDirBuilder
from appimage_builder.bundler.tools import run_appimagetool, run_linuxdeploy, sign_appimage
from appimage_builder.core.constants import BuildStage
from appimage_builder.core.exceptions import BuildError, CancellationError
from appimage_builder.core.models import (
    BuildConfig,
    BuildProgress,
    ProjectConfig,
    RuntimeConfig,
)
from appimage_builder.core.services.project_service import find_project_root
from appimage_builder.core.services.template_service import TemplateService
from appimage_builder.runtime.manager import RuntimeManager


class BuildService:
    """Servicio puro de negocio para orquestar el build completo."""

    def __init__(
        self,
        project: ProjectConfig,
        build: BuildConfig,
        project_root: Path | None = None,
        runtime: RuntimeConfig | None = None,
    ) -> None:
        self.project_config = project
        self.build_config = build
        self.project_root = project_root or find_project_root()
        self.runtime_config = runtime or RuntimeConfig()
        self.runtime_manager = RuntimeManager(self.runtime_config, architecture=build.architecture)
        self.templates = TemplateService()

        # Directorios de trabajo
        self._work_dir: Path | None = None
        self._appdir: Path | None = None
        self._built_artifact: Path | None = None

    @property
    def work_dir(self) -> Path:
        if self._work_dir is None:
            self._work_dir = Path(tempfile.mkdtemp(prefix="appimage-build-"))
        return self._work_dir

    @property
    def appdir(self) -> Path:
        if self._appdir is None:
            self._appdir = self.work_dir / "AppDir"
        return self._appdir

    @property
    def output_path(self) -> Path:
        return (
            self.build_config.output
            / f"{self.project_config.name}-{self.build_config.architecture.value}.AppImage"
        )

    async def build(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path:
        """
        Ejecuta el build completo.

        Args:
            progress_callback: Callback async para reportar progreso
            cancel_event: Event para cancelación cooperativa

        Returns:
            Path al AppImage generado (o ruta esperada si las herramientas
            externas no estaban disponibles).
        """
        stages = [
            (BuildStage.PREPARING, self._prepare_appdir),
            (BuildStage.DOWNLOADING_RUNTIME, self._download_runtimes),
            (BuildStage.INSTALLING_DEPS, self._install_dependencies),
            (BuildStage.RUNNING_LINUXDEPLOY, self._run_linuxdeploy),
            (BuildStage.CREATING_APPIMAGE, self._run_appimagetool),
            (BuildStage.SIGNING, self._sign_if_needed),
        ]

        total_stages = len(stages)

        for i, (stage, step_fn) in enumerate(stages):
            if cancel_event and cancel_event.is_set():
                raise CancellationError()

            base_progress = i / total_stages
            await self._report(
                progress_callback,
                stage,
                base_progress,
                f"Iniciando {stage.value}...",
            )

            try:
                await step_fn(progress_callback, cancel_event)
            except CancellationError:
                raise
            except Exception as e:
                raise BuildError(
                    f"Error en etapa {stage.value}: {e}",
                    stage=stage.value,
                    hint="Revisa los logs detallados para más información",
                ) from e

        await self._report(
            progress_callback,
            BuildStage.COMPLETED,
            1.0,
            "¡Build completado exitosamente!",
        )

        return self._finalize_output()

    def _finalize_output(self) -> Path:
        """Copia el artefacto real a la ruta de salida final."""
        target = self.output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if self._built_artifact is not None and self._built_artifact.exists():
            if self._built_artifact.resolve() != target.resolve():
                shutil.copy2(self._built_artifact, target)
        return target

    async def _report(
        self,
        callback: Callable[[BuildProgress], Awaitable[None]] | None,
        stage: BuildStage,
        progress: float,
        message: str,
        details: str = "",
    ) -> None:
        if callback:
            await callback(
                BuildProgress(
                    stage=stage.value,
                    progress=progress,
                    message=message,
                    details=details,
                )
            )

    async def _prepare_appdir(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Prepara la estructura AppDir (delega en AppDirBuilder)."""
        await self._report(
            progress_callback,
            BuildStage.PREPARING,
            0.1,
            "Creando estructura AppDir...",
        )

        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)
        self.appdir.mkdir(parents=True, exist_ok=True)

        await self._report(
            progress_callback,
            BuildStage.PREPARING,
            0.5,
            "Generando archivos base...",
        )

        builder = AppDirBuilder(
            project=self.project_config,
            build=self.build_config,
            appdir=self.appdir,
            templates=self.templates,
        )
        await asyncio.to_thread(builder.build_base)

        await self._report(
            progress_callback,
            BuildStage.PREPARING,
            1.0,
            "Estructura AppDir preparada",
        )

    async def _download_runtimes(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Garantiza linuxdeploy y appimagetool en cache."""
        await self._report(
            progress_callback,
            BuildStage.DOWNLOADING_RUNTIME,
            0.2,
            "Verificando runtimes en cache...",
        )

        async def forward(update: BuildProgress) -> None:
            # El manager ya emite fracción 0..1 dentro de la etapa.
            await self._report(
                progress_callback,
                BuildStage.DOWNLOADING_RUNTIME,
                update.progress,
                update.message,
                update.details,
            )

        await self.runtime_manager.ensure_all(progress=forward)

        await self._report(
            progress_callback,
            BuildStage.DOWNLOADING_RUNTIME,
            1.0,
            "Runtimes listos",
        )

    async def _install_dependencies(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Instala el payload según el tipo de proyecto (builders Fase 3)."""
        from appimage_builder.builders.factory import get_builder

        await self._report(
            progress_callback,
            BuildStage.INSTALLING_DEPS,
            0.1,
            f"Instalando payload ({self.project_config.build_type.value})...",
        )

        async def forward(update: BuildProgress) -> None:
            await self._report(
                progress_callback,
                BuildStage.INSTALLING_DEPS,
                update.progress,
                update.message,
                update.details,
            )

        builder = get_builder(
            self.project_config.build_type,
            project=self.project_config,
            build=self.build_config,
            project_root=self.project_root,
        )
        await builder.install(appdir=self.appdir, progress=forward, cancel_event=cancel_event)

        await self._report(
            progress_callback,
            BuildStage.INSTALLING_DEPS,
            1.0,
            "Payload instalado",
        )

    def _desktop_file(self) -> Path:
        return self.appdir / f"{self.project_config.name}.desktop"

    def _icon_file(self) -> Path | None:
        if self.project_config.icon:
            suffix = self.project_config.icon.suffix or ".png"
            candidate = self.appdir / f"{self.project_config.name}{suffix}"
            if candidate.exists():
                return candidate
        candidates = sorted(self.appdir.glob("*.png")) + sorted(self.appdir.glob("*.svg"))
        return candidates[0] if candidates else None

    async def _run_linuxdeploy(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Ejecuta linuxdeploy si está disponible; si no, lo omite."""
        if not self.runtime_manager.is_linuxdeploy_available():
            await self._report(
                progress_callback,
                BuildStage.RUNNING_LINUXDEPLOY,
                1.0,
                "linuxdeploy no disponible: etapa omitida",
            )
            return

        await self._report(
            progress_callback,
            BuildStage.RUNNING_LINUXDEPLOY,
            0.2,
            "Ejecutando linuxdeploy...",
        )

        async def forward(update: BuildProgress) -> None:
            await self._report(
                progress_callback,
                BuildStage.RUNNING_LINUXDEPLOY,
                update.progress,
                update.message,
                update.details,
            )

        await run_linuxdeploy(
            linuxdeploy=self.runtime_manager.resolve_linuxdeploy(),
            appdir=self.appdir,
            desktop_file=self._desktop_file(),
            icon_file=self._icon_file(),
            apprun_file=self.appdir / "AppRun",
            project=self.project_config,
            build=self.build_config,
            no_fuse=self.runtime_config.no_fuse,
            progress=forward,
            cancel_event=cancel_event,
        )
        await asyncio.to_thread(self._repair_root_files)
        await self._report(
            progress_callback,
            BuildStage.RUNNING_LINUXDEPLOY,
            1.0,
            "linuxdeploy completado",
        )

    def _repair_root_files(self) -> None:
        """Restaura archivos raíz que linuxdeploy deja como symlinks rotos.

        linuxdeploy redespliega .desktop/icono/AppRun a la raíz; si ya
        existían, puede dejar symlinks a sí mismos. Como las copias en usr/
        también son symlinks a la raíz, se regenera/copia desde fuentes reales.
        """
        name = self.project_config.name

        apprun = self.appdir / "AppRun"
        if not apprun.exists() or apprun.is_symlink():
            backup = self.appdir.parent / "CustomAppRun"
            if backup.exists():
                if apprun.is_symlink() or apprun.exists():
                    apprun.unlink(missing_ok=True)
                shutil.copy2(backup, apprun)
                apprun.chmod(0o755)

        desktop = self.appdir / f"{name}.desktop"
        if not desktop.exists() or desktop.is_symlink():
            desktop.unlink(missing_ok=True)
            self.templates.write_desktop_entry(self.project_config, self.build_config, desktop)

        for suffix in (".png", ".svg"):
            icon = self.appdir / f"{name}{suffix}"
            if icon.exists() and not icon.is_symlink():
                break
            candidates = sorted(
                p
                for p in (self.appdir / "usr/share/icons").rglob(f"{name}{suffix}")
                if p.is_file() and not p.is_symlink()
            )
            if candidates:
                icon.unlink(missing_ok=True)
                shutil.copy2(candidates[0], icon)
                break

    async def _run_appimagetool(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Convierte el AppDir en AppImage si la herramienta existe."""
        if not self.runtime_manager.is_appimagetool_available():
            await self._report(
                progress_callback,
                BuildStage.CREATING_APPIMAGE,
                1.0,
                "appimagetool no disponible: artefacto pendiente",
            )
            self._built_artifact = None
            return

        await self._report(
            progress_callback,
            BuildStage.CREATING_APPIMAGE,
            0.2,
            "Creando AppImage con appimagetool...",
        )

        async def forward(update: BuildProgress) -> None:
            await self._report(
                progress_callback,
                BuildStage.CREATING_APPIMAGE,
                update.progress,
                update.message,
                update.details,
            )

        # Construir en el work_dir y luego copiar a la salida final.
        tmp_output = self.work_dir / self.output_path.name
        artifact = await run_appimagetool(
            appimagetool=self.runtime_manager.resolve_appimagetool(),
            appdir=self.appdir,
            output=tmp_output,
            project=self.project_config,
            build=self.build_config,
            no_fuse=self.runtime_config.no_fuse,
            progress=forward,
            cancel_event=cancel_event,
        )
        self._built_artifact = artifact

        # Hook post-install con APPIMAGE disponible.
        if self.build_config.post_install_hook is not None:
            await asyncio.to_thread(self._run_post_install_hook, artifact)

        await self._report(
            progress_callback,
            BuildStage.CREATING_APPIMAGE,
            1.0,
            "AppImage creado",
        )

    def _run_post_install_hook(self, artifact: Path) -> None:
        from appimage_builder.utils.hooks import run_hook_script

        hook = self.build_config.post_install_hook
        assert hook is not None
        run_hook_script(
            hook,
            name="post-install",
            stage="creating_appimage",
            cwd=self.appdir,
            extra_env={"APPIMAGE": str(artifact), "APPDIR": str(self.appdir)},
        )

    async def _sign_if_needed(
        self,
        progress_callback: Callable[[BuildProgress], Awaitable[None]] | None,
        cancel_event: asyncio.Event | None,
    ) -> None:
        """Firma el AppImage si está configurado y existe el artefacto."""
        if not self.build_config.sign:
            await self._report(
                progress_callback,
                BuildStage.SIGNING,
                1.0,
                "Firma omitida (no configurada)",
            )
            return

        target = self._built_artifact or self.output_path
        if not target.exists():
            await self._report(
                progress_callback,
                BuildStage.SIGNING,
                1.0,
                "Sin artefacto: firma omitida",
            )
            return

        await self._report(
            progress_callback,
            BuildStage.SIGNING,
            0.5,
            "Firmando AppImage...",
        )

        async def forward(update: BuildProgress) -> None:
            await self._report(
                progress_callback,
                BuildStage.SIGNING,
                update.progress,
                update.message,
                update.details,
            )

        await sign_appimage(
            appimage=target,
            sign_key=self.build_config.sign_key,
            progress=forward,
        )
        await self._report(
            progress_callback,
            BuildStage.SIGNING,
            1.0,
            "AppImage firmado",
        )

    def cleanup(self) -> None:
        """Limpia directorios temporales."""
        if self._work_dir and self._work_dir.exists():
            shutil.rmtree(self._work_dir, ignore_errors=True)
            self._work_dir = None
            self._appdir = None

    def __del__(self) -> None:
        self.cleanup()
