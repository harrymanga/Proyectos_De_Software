"""Opciones CLI compartidas y resolución de configuración."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from appimage_builder.core.config import CLISettings, ConfigManager
from appimage_builder.core.constants import Architecture, BuildType, Compression
from appimage_builder.core.exceptions import AppImageBuilderError
from appimage_builder.core.models import AppImageBuilderConfig

console = Console()
err_console = Console(stderr=True)

# --- Tipos de opción reutilizables ---

ConfigOpt = Annotated[
    Path | None,
    typer.Option(
        "--config",
        "-c",
        help="Archivo pyproject.toml con [tool.appimage-builder].",
        exists=False,
        dir_okay=False,
        resolve_path=True,
    ),
]

ProjectPathOpt = Annotated[
    Path,
    typer.Option(
        "--project-path",
        "-p",
        help="Directorio raíz del proyecto a empaquetar.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
]

NameOpt = Annotated[str | None, typer.Option("--name", help="Nombre de la aplicación.")]
VersionOpt = Annotated[str | None, typer.Option("--version", help="Versión semántica (ej: 1.0.0).")]
EntryPointOpt = Annotated[
    str | None,
    typer.Option("--entry-point", help="Entry point (Python: modulo:funcion, nativo: binario)."),
]
BuildTypeOpt = Annotated[
    BuildType | None,
    typer.Option("--build-type", help="Tipo de proyecto.", case_sensitive=False),
]
OutputOpt = Annotated[
    Path | None,
    typer.Option("--output", "-o", help="Directorio de salida del AppImage."),
]
ArchOpt = Annotated[
    Architecture | None,
    typer.Option("--arch", help="Arquitectura objetivo.", case_sensitive=False),
]
CompressionOpt = Annotated[
    Compression | None,
    typer.Option("--compression", help="Compresión SquashFS.", case_sensitive=False),
]
VerboseOpt = Annotated[bool, typer.Option("--verbose", "-v", help="Salida detallada.")]
QuietOpt = Annotated[bool, typer.Option("--quiet", "-q", help="Solo errores.")]
DryRunOpt = Annotated[
    bool, typer.Option("--dry-run", help="Muestra la configuración sin construir.")
]


def build_cli_settings(**kwargs: Any) -> CLISettings:
    """Construye CLISettings filtrando valores None no relevantes."""
    return CLISettings(**kwargs)


def resolve_config(
    config_file: Path | None = None,
    project_path: Path | None = None,
    cli_kwargs: dict[str, Any] | None = None,
) -> tuple[AppImageBuilderConfig, ConfigManager]:
    """Resuelve la configuración final con precedencia CLI > ENV > TOML > defaults.

    Args:
        config_file: ruta explícita al pyproject.toml (o None para autodetectar).
        project_path: raíz del proyecto (para buscar pyproject.toml vecino).
        cli_kwargs: overrides de línea de comandos (nombres de CLISettings).

    Returns:
        Tupla (config_final, manager).
    """
    manager = ConfigManager()

    # 1. TOML: explícito > <project_path>/pyproject.toml > ./pyproject.toml
    candidates: list[Path] = []
    if config_file is not None:
        candidates.append(config_file)
    if project_path is not None:
        candidates.append(project_path / "pyproject.toml")
    candidates.append(Path.cwd() / "pyproject.toml")

    toml_config = None
    for candidate in candidates:
        if candidate.exists():
            loaded = manager.load_toml(candidate)
            if loaded is not None:
                toml_config = loaded
                break
            # Existe pero sin sección nuestra: seguir con el siguiente candidato,
            # salvo que el usuario lo haya pedido explícitamente.
            if config_file is not None and candidate == config_file:
                break

    # 2. ENV
    env_config = manager.load_env()

    # 3. CLI
    cli_settings = manager.load_cli(**(cli_kwargs or {}))

    final = manager.merge(
        toml_config=toml_config,
        cli_settings=cli_settings,
        env_config=env_config,
    )
    return final, manager


def handle_error(e: Exception) -> int:
    """Imprime un error de forma amigable y devuelve el exit code."""
    from rich.markup import escape

    if isinstance(e, AppImageBuilderError):
        err_console.print(f"[bold red]Error:[/bold red] {escape(e.message)}")
        if e.hint:
            err_console.print(f"[yellow]💡 {escape(e.hint)}[/yellow]")
        if e.details:
            err_console.print(f"[dim]{escape(e.details)}[/dim]")
        return e.exit_code
    err_console.print(f"[bold red]Error inesperado:[/bold red] {escape(str(e))}")
    return 1


def print_config_summary(config: AppImageBuilderConfig) -> None:
    """Muestra un resumen Rich de la configuración resuelta."""
    console.print("[bold]Configuración resuelta[/bold]")
    console.print(
        f"  Proyecto: [cyan]{config.project.name}[/cyan] "
        f"[dim]{config.project.version}[/dim] "
        f"({config.project.build_type.value})"
    )
    console.print(f"  Entry point: [cyan]{config.project.entry_point or '(vacío)'}[/cyan]")
    console.print(
        f"  Salida: [cyan]{config.build.output}[/cyan] "
        f"| arch: [cyan]{config.build.architecture.value}[/cyan] "
        f"| compresión: [cyan]{config.build.compression.value}[/cyan]"
    )
    console.print(f"  Cache: [dim]{config.runtime.cache_dir}[/dim]")
