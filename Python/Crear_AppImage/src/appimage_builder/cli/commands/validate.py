"""Comando `validate`: valida configuración y/o estructura AppDir."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from appimage_builder.cli.options import (
    ConfigOpt,
    ProjectPathOpt,
    console,
    handle_error,
    resolve_config,
)
from appimage_builder.core.models import ValidationResult
from appimage_builder.validators.appdir import validate_appdir
from appimage_builder.validators.appstream import validate_metainfo_file
from appimage_builder.validators.desktop import validate_desktop_file
from appimage_builder.validators.project import validate_project_config

app = typer.Typer(help="Valida la configuración y la estructura AppDir.")


@app.callback(invoke_without_command=True)
def validate(
    ctx: typer.Context,
    config: ConfigOpt = None,
    project_path: ProjectPathOpt = Path.cwd(),
    appdir: Path | None = typer.Option(
        None, "--appdir", help="Directorio AppDir a validar.", resolve_path=True
    ),
    desktop: Path | None = typer.Option(
        None, "--desktop", help="Archivo .desktop suelto a validar.", resolve_path=True
    ),
    metainfo: Path | None = typer.Option(
        None, "--metainfo", help="XML AppStream suelto a validar.", resolve_path=True
    ),
) -> None:
    """Valida que la configuración y el AppDir cumplan el estándar."""
    del ctx
    try:
        result = ValidationResult(valid=True)

        # 1. Configuración (siempre)
        try:
            final, _ = resolve_config(config_file=config, project_path=project_path.resolve())
            result = validate_project_config(final, result)
        except Exception as e:
            result = result.add_error(f"Configuración inválida: {e}")

        # 2. AppDir y/o archivos sueltos
        if appdir is not None:
            result = validate_appdir(appdir, result)
        if desktop is not None:
            result = validate_desktop_file(desktop, result)
        if metainfo is not None:
            result = validate_metainfo_file(metainfo, result)
        if appdir is None and desktop is None and metainfo is None:
            result = result.add_info("Sin --appdir/--desktop/--metainfo: solo se validó la config.")

        _print_result(result)
        if not result.valid:
            raise typer.Exit(code=80)
    except typer.Exit:
        raise
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


def _print_result(result: ValidationResult) -> None:
    from rich.markup import escape

    table = Table(title="Resultado de validación")
    table.add_column("Nivel", style="bold")
    table.add_column("Mensaje")
    for msg in result.errors:
        table.add_row("[red]ERROR[/red]", escape(msg))
    for msg in result.warnings:
        table.add_row("[yellow]WARN[/yellow]", escape(msg))
    for msg in result.info:
        table.add_row("[green]INFO[/green]", escape(msg))
    console.print(table)
    if result.valid:
        console.print("[bold green]✅ Validación exitosa[/bold green]")
    else:
        console.print("[bold red]❌ Validación fallida[/bold red]")
