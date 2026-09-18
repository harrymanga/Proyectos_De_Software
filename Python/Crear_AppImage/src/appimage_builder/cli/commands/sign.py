"""Comando `sign`: firma un AppImage existente con GPG."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from appimage_builder.bundler.tools import sign_appimage
from appimage_builder.cli.options import console, handle_error

app = typer.Typer(help="Firma un AppImage existente con GPG.")


@app.callback(invoke_without_command=True)
def sign(
    ctx: typer.Context,
    appimage: Path = typer.Argument(
        ..., help="AppImage a firmar.", exists=True, dir_okay=False, resolve_path=True
    ),
    key: str | None = typer.Option(None, "--key", "-k", help="Key ID GPG (vacío = por defecto)."),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Ruta del .sig (defecto: <app>.sig)."
    ),
) -> None:
    """Genera `<app>.sig` con `gpg --detach-sign --armor`."""
    del ctx
    try:
        sig = asyncio.run(sign_appimage(appimage=appimage, sign_key=key))
        if output is not None and output.resolve() != sig.resolve():
            output.parent.mkdir(parents=True, exist_ok=True)
            sig.replace(output)
            sig = output
        console.print(f"[bold green]✅ Firmado:[/bold green] {sig}")
    except typer.Exit:
        raise
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None
