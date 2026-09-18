"""Comando `build`: construye el AppImage."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from appimage_builder.cli.options import (
    ArchOpt,
    BuildTypeOpt,
    CompressionOpt,
    ConfigOpt,
    DryRunOpt,
    EntryPointOpt,
    NameOpt,
    OutputOpt,
    ProjectPathOpt,
    QuietOpt,
    VerboseOpt,
    VersionOpt,
    console,
    handle_error,
    print_config_summary,
    resolve_config,
)
from appimage_builder.core.constants import BuildStage, ExitCode
from appimage_builder.core.models import BuildProgress
from appimage_builder.core.services.build_service import BuildService
from appimage_builder.core.services.project_service import find_project_root

app = typer.Typer(help="Construye el AppImage.")


@app.callback(invoke_without_command=True)
def build(
    ctx: typer.Context,
    config: ConfigOpt = None,
    project_path: ProjectPathOpt = Path.cwd(),
    name: NameOpt = None,
    version: VersionOpt = None,
    entry_point: EntryPointOpt = None,
    build_type: BuildTypeOpt = None,
    output: OutputOpt = None,
    arch: ArchOpt = None,
    compression: CompressionOpt = None,
    icon: Path | None = typer.Option(None, help="Icono PNG/SVG de la aplicación."),
    python_version: str | None = typer.Option(
        None, help="Versión de Python del payload (ej: 3.11)."
    ),
    gui_entry_point: str | None = typer.Option(
        None, "--gui-entry-point", help="Entry GUI: AppRun --gui la lanza (Python: modulo:funcion)."
    ),
    sign: bool | None = typer.Option(None, help="Firmar con GPG."),
    sign_key: str | None = typer.Option(None, help="Key ID de GPG para firmar."),
    exclude_library: list[str] | None = typer.Option(
        None, "--exclude-library", help="Librería a excluir en linuxdeploy (repetible)."
    ),
    linuxdeploy: Path | None = typer.Option(
        None, "--linuxdeploy", help="Binario local de linuxdeploy (sin descarga)."
    ),
    appimagetool: Path | None = typer.Option(
        None, "--appimagetool", help="Binario local de appimagetool (sin descarga)."
    ),
    bundle_tree: bool | None = typer.Option(
        None, "--bundle-tree/--no-bundle-tree", help="Genérico: empaqueta todo el árbol."
    ),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
    dry_run: DryRunOpt = False,
) -> None:
    """Construye el AppImage del proyecto."""
    # Permitir `appimage-builder build` y `appimage-builder --opt` (comando por defecto).
    # Si se invoca como subcomando con extras, Typer lo maneja; este callback es el build.
    del ctx  # no usamos sub-subcomandos aquí
    try:
        root = project_path.resolve() if project_path else find_project_root()
        final, _ = resolve_config(
            config_file=config,
            project_path=root,
            cli_kwargs={
                "project_name": name,
                "project_version": version,
                "entry_point": entry_point,
                "build_type": build_type,
                "output": output,
                "architecture": arch,
                "compression": compression,
                "icon": icon,
                "python_version": python_version,
                "gui_entry_point": gui_entry_point,
                "sign": sign,
                "sign_key": sign_key,
                "excluded_libraries": list(exclude_library or []),
                "linuxdeploy_path": linuxdeploy,
                "appimagetool_path": appimagetool,
                "bundle_tree": bundle_tree,
                "verbose": verbose,
                "quiet": quiet,
                "dry_run": dry_run,
            },
        )
        if output is None and config is None:
            # Sin TOML ni --output: el dist vive junto al proyecto, no en el CWD.
            final.build.output = root / "dist"

        if not quiet:
            print_config_summary(final)

        if dry_run:
            console.print("[yellow]Dry-run: no se construyó nada.[/yellow]")
            return

        final.build.output.mkdir(parents=True, exist_ok=True)

        service = BuildService(
            project=final.project,
            build=final.build,
            project_root=root,
            runtime=final.runtime,
        )
        exit_code = asyncio.run(_run_with_progress(service, verbose=verbose, quiet=quiet))
        if exit_code != ExitCode.SUCCESS:
            raise typer.Exit(code=int(exit_code))
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]Build cancelado por el usuario.[/yellow]")
        raise typer.Exit(code=int(ExitCode.CANCELLED)) from None
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


async def _run_with_progress(
    service: BuildService, *, verbose: bool = False, quiet: bool = False
) -> ExitCode:
    """Ejecuta el build mostrando progreso Rich en tiempo real."""
    stage_order = [
        BuildStage.PREPARING.value,
        BuildStage.DOWNLOADING_RUNTIME.value,
        BuildStage.INSTALLING_DEPS.value,
        BuildStage.RUNNING_LINUXDEPLOY.value,
        BuildStage.CREATING_APPIMAGE.value,
        BuildStage.SIGNING.value,
    ]

    if quiet:
        # Sin barra: solo ejecutar y reportar el resultado final.
        async def silent_cb(_: BuildProgress) -> None:
            return None

        try:
            output = await service.build(progress_callback=silent_cb)
        finally:
            service.cleanup()
        console.print(f"[green]✅ AppImage: {output}[/green]")
        return ExitCode.SUCCESS

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        tasks = {stage: progress.add_task(stage, total=100.0) for stage in stage_order}

        async def rich_cb(update: BuildProgress) -> None:
            from rich.markup import escape

            if update.stage in tasks:
                task_id = tasks[update.stage]
                progress.update(
                    task_id,
                    completed=max(0.0, min(1.0, update.progress)) * 100.0,
                    description=f"{update.stage}: {escape(update.message)}",
                )
            elif verbose and update.message:
                console.print(f"[dim]{update.stage}: {escape(update.message)}[/dim]")

        try:
            output = await service.build(progress_callback=rich_cb)
        finally:
            service.cleanup()

    console.print(f"[bold green]✅ AppImage generado:[/bold green] {output}")
    return ExitCode.SUCCESS
