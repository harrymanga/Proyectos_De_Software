"""Ensamblado de la aplicación CLI (Typer + Rich)."""

from __future__ import annotations

import typer

from appimage_builder import __version__
from appimage_builder.cli import spanish as _spanish  # noqa: F401 - aplica ayuda en español
from appimage_builder.cli.commands import build as build_mod
from appimage_builder.cli.commands import doctor as doctor_mod
from appimage_builder.cli.commands import init as init_mod
from appimage_builder.cli.commands import sign as sign_mod
from appimage_builder.cli.commands import template as template_mod
from appimage_builder.cli.commands import validate as validate_mod

app = typer.Typer(
    name="appimage-builder",
    help="Crea AppImages de forma automatizada (CLI intuitiva).",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)


def _version(value: bool) -> None:
    if value:
        typer.echo(f"appimage-builder {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        help="Muestra la versión y sale.",
        callback=_version,
        is_eager=True,
    ),
) -> None:
    """Opciones globales (ver cada comando para más detalle)."""
    del version


# Subcomandos: cada módulo expone un Typer con callback único.
app.add_typer(build_mod.app, name="build", help="Construye el AppImage.")
app.add_typer(init_mod.app, name="init", help="Inicializa la configuración.")
app.add_typer(validate_mod.app, name="validate", help="Valida config y AppDir.")
app.add_typer(doctor_mod.app, name="doctor", help="Diagnostica el entorno.")
app.add_typer(sign_mod.app, name="sign", help="Firma un AppImage con GPG.")
app.add_typer(template_mod.app, name="template", help="Gestiona plantillas guardadas.")


def main() -> None:
    """Entry point console-script (ayuda integrada en español vía cli.spanish)."""
    app()


if __name__ == "__main__":
    main()
