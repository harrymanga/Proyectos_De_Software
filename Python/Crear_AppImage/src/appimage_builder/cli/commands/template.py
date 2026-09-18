"""Comando `template`: guarda/lista/borra plantillas de configuración."""

from __future__ import annotations

from pathlib import Path

import typer

from appimage_builder.cli.options import (
    ConfigOpt,
    ProjectPathOpt,
    console,
    handle_error,
    resolve_config,
)
from appimage_builder.core.services.template_store import TemplateStore

app = typer.Typer(help="Gestiona plantillas de configuración guardadas.")


@app.command("save")
def save(
    name: str = typer.Argument(..., help="Nombre de la plantilla."),
    config: ConfigOpt = None,
    project_path: ProjectPathOpt = Path.cwd(),
) -> None:
    """Guarda la configuración resuelta actual como plantilla."""
    try:
        final, _ = resolve_config(config_file=config, project_path=project_path.resolve())
        dest = TemplateStore().save(name, final)
        console.print(f"[green]✅ Plantilla {name!r} guardada en {dest}[/green]")
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


@app.command("list")
def list_templates() -> None:
    """Lista las plantillas guardadas."""
    try:
        names = TemplateStore().list_names()
        if not names:
            console.print("[dim]No hay plantillas guardadas.[/dim]")
            return
        for name in names:
            console.print(f"  • {name}")
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


@app.command("show")
def show(name: str = typer.Argument(..., help="Nombre de la plantilla.")) -> None:
    """Muestra una plantilla en TOML."""
    try:
        import tomli_w

        config = TemplateStore().load(name)
        console.print(tomli_w.dumps(config.model_dump(mode="json", exclude_none=True)))
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


@app.command("delete")
def delete(name: str = typer.Argument(..., help="Nombre de la plantilla.")) -> None:
    """Borra una plantilla guardada."""
    try:
        TemplateStore().delete(name)
        console.print(f"[green]✅ Plantilla {name!r} borrada.[/green]")
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None
