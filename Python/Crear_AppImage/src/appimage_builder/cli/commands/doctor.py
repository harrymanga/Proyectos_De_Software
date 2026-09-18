"""Comando `doctor`: diagnostica el entorno del sistema."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.table import Table

from appimage_builder.cli.options import console, handle_error
from appimage_builder.core.constants import DEFAULT_CACHE_DIR

app = typer.Typer(help="Diagnostica el entorno (dependencias, FUSE, cache).")

_MIN_FREE_BYTES = 1_000_000_000  # 1 GiB en cache


@app.callback(invoke_without_command=True)
def doctor(
    ctx: typer.Context,
    as_json: bool = typer.Option(False, "--json", help="Salida en JSON (para scripts)."),
) -> None:
    """Revisa dependencias del sistema y muestra cómo corregirlas."""
    del ctx
    try:
        rows: list[tuple[str, str, str]] = []

        # Python
        py_ok = sys.version_info >= (3, 11)
        rows.append(("Python >= 3.11", "OK" if py_ok else "FAIL", platform.python_version()))

        # Plataforma
        is_linux = sys.platform.startswith("linux")
        rows.append(
            (
                "Sistema Linux",
                "OK" if is_linux else "FAIL",
                f"{platform.system()} {platform.machine()}",
            )
        )

        # FUSE (necesario para ejecutar AppImages)
        fusermount = shutil.which("fusermount") or shutil.which("fusermount3")
        rows.append(
            (
                "FUSE (fusermount)",
                "OK" if fusermount else "WARN",
                fusermount
                or "no encontrado; podrás crear AppImages pero no ejecutarlos sin --appimage-extract",
            )
        )

        # Herramientas opcionales
        for tool in (
            "gcc",
            "make",
            "cmake",
            "cargo",
            "go",
            "gpg",
            "pip",
            "desktop-file-validate",
            "appstreamcli",
        ):
            path = shutil.which(tool)
            rows.append(
                (
                    f" Herramienta: {tool}",
                    "OK" if path else "WARN",
                    path or "no encontrada (opcional según tipo de proyecto)",
                )
            )

        # Versión de pip (útil para builders Python)
        rows.append(("pip funcional", *_check_pip()))

        # Cache escribible
        cache = DEFAULT_CACHE_DIR
        try:
            cache.mkdir(parents=True, exist_ok=True)
            probe = cache / ".write-test"
            probe.touch()
            probe.unlink()
            rows.append(("Cache escribible", "OK", str(cache)))
        except OSError as e:
            rows.append(("Cache escribible", "FAIL", str(e)))

        # Espacio libre en cache
        rows.append(("Espacio en cache", *_check_disk(cache)))

        if as_json:
            # soft_wrap: Rich no debe partir líneas largas del JSON.
            console.print(
                json.dumps(
                    [
                        {"check": name, "status": status, "detail": detail}
                        for name, status, detail in rows
                    ],
                    indent=2,
                    ensure_ascii=False,
                ),
                soft_wrap=True,
            )
        else:
            _print_table(rows)

        if any(s == "FAIL" for _, s, _ in rows):
            if not as_json:
                console.print("[red]Hay fallos críticos. Corrige lo marcado como FAIL.[/red]")
            raise typer.Exit(code=1)
        if not as_json:
            console.print("[green]Entorno listo (avisos WARN son opcionales).[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        raise typer.Exit(code=handle_error(e)) from None


def _check_pip() -> tuple[str, str]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return ("WARN", f"pip no ejecutable: {e}.")
    if proc.returncode != 0:
        return ("WARN", "pip falló (python3 -m ensurepip para repararlo).")
    return ("OK", proc.stdout.strip().splitlines()[0] if proc.stdout else "pip disponible.")


def _check_disk(path: Path) -> tuple[str, str]:
    try:
        usage = shutil.disk_usage(path if path.exists() else Path.home())
    except OSError as e:
        return ("WARN", f"No se pudo medir el disco: {e}.")
    free_gib = usage.free / (1024**3)
    detail = f"{free_gib:.1f} GiB libres en {path}."
    if usage.free < _MIN_FREE_BYTES:
        return ("WARN", detail + " Recomendado: ≥1 GiB para runtimes y builds.")
    return ("OK", detail)


def _print_table(rows: list[tuple[str, str, str]]) -> None:
    table = Table(title="Doctor: diagnóstico del entorno")
    table.add_column("Chequeo", style="bold")
    table.add_column("Estado")
    table.add_column("Detalle", overflow="fold")
    for name, status, detail in rows:
        if status == "OK":
            style = "[green]OK[/green]"
        elif status == "WARN":
            style = "[yellow]WARN[/yellow]"
        else:
            style = "[red]FAIL[/red]"
        table.add_row(name, style, detail)
    console.print(table)
