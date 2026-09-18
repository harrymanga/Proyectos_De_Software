"""Comando `init`: detecta el proyecto y genera la configuración inicial."""

from __future__ import annotations

import tomllib
from pathlib import Path

import typer

from appimage_builder.cli.options import ProjectPathOpt, console, handle_error
from appimage_builder.core.config import create_default_config

app = typer.Typer(help="Inicializa la configuración de appimage-builder.")


@app.callback(invoke_without_command=True)
def init(
    ctx: typer.Context,
    project_path: ProjectPathOpt = Path.cwd(),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescribe la sección existente."),
    stdout: bool = typer.Option(
        False, "--stdout", help="Imprime el TOML en stdout en lugar de escribirlo."
    ),
    from_template: str | None = typer.Option(
        None, "--from-template", help="Parte de una plantilla guardada en vez de detectar."
    ),
) -> None:
    """Detecta el tipo de proyecto y escribe [tool.appimage-builder]."""
    del ctx
    try:
        root = project_path.resolve()
        if from_template is not None:
            from appimage_builder.core.services.template_store import TemplateStore

            base = TemplateStore().load(from_template)
            config = base.model_copy(deep=True)
            # El nombre/output siguen al proyecto destino, no a la plantilla.
            config.project.name = root.name
            config.build.output = root / "dist"
            console.print(f"Plantilla base: [cyan]{from_template}[/cyan]")
        else:
            config = create_default_config(root)
            console.print(
                f"Detectado: [cyan]{config.project.build_type.value}[/cyan] "
                f"entry_point=[cyan]{config.project.entry_point or '(vacío)'}[/cyan]"
            )

        block = {
            "project": {
                "name": config.project.name,
                "version": config.project.version,
                "description": config.project.description,
                "author": config.project.author,
                "license": config.project.license,
                "build_type": config.project.build_type.value,
                "entry_point": config.project.entry_point,
                "python_version": config.project.python_version,
            },
            "build": {
                "output": str(config.build.output),
                "architecture": config.build.architecture.value,
                "compression": config.build.compression.value,
            },
            "runtime": {"cache_dir": str(config.runtime.cache_dir)},
        }

        if stdout:
            import tomli_w

            console.print(tomli_w.dumps({"tool": {"appimage-builder": block}}))
            return

        target = root / "pyproject.toml"
        if target.exists():
            with target.open("rb") as f:
                data = tomllib.load(f)
            tool = data.setdefault("tool", {})
            if "appimage-builder" in tool and not force:
                console.print(
                    f"[yellow]Ya existe [tool.appimage-builder] en {target}. "
                    "Usa --force para sobrescribir.[/yellow]"
                )
                return
            tool["appimage-builder"] = block
        else:
            data = {"tool": {"appimage-builder": block}}

        import tomli_w

        with target.open("wb") as f:
            tomli_w.dump(data, f)
        console.print(f"[green]✅ Configuración escrita en {target}[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None
