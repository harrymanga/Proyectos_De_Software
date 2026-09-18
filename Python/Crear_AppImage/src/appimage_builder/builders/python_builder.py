"""Builder Python: `pip install --target` + wrapper en `usr/bin`."""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

from appimage_builder.builders.base import BaseBuilder, ProgressCb
from appimage_builder.bundler.tools import stream_command

_WRAPPER_TEMPLATE = """#!/usr/bin/env python3
\"\"\"Lanzador generado por appimage-builder para {name}.\"\"\"
import glob
import os
import sys


def _site_packages() -> list[str]:
    appdir = os.environ.get("APPDIR", "")
    candidates = []
    if appdir:
        candidates.extend(
            glob.glob(os.path.join(appdir, "usr", "lib", "python*", "site-packages"))
        )
    here = os.path.dirname(os.path.realpath(__file__))
    candidates.extend(
        glob.glob(os.path.join(here, "..", "lib", "python*", "site-packages"))
    )
    seen = []
    for path in candidates:
        if path not in seen:
            seen.append(path)
    return seen


def main() -> int:
    for path in _site_packages():
        if path not in sys.path:
            sys.path.insert(0, path)
    os.environ.setdefault("PYTHONNOUSERSITE", "1")
    from {module} import {func}  # type: ignore[attr-defined]

    result = {func}()
    if isinstance(result, int):
        return result
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""


class PythonBuilder(BaseBuilder):
    """Empaqueta un proyecto Python con pip y genera el wrapper lanzador."""

    async def install(
        self,
        *,
        appdir: Path,
        progress: ProgressCb = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path | None:
        module, func = self._split_entry(
            self.project.entry_point, field="entry_point", example="main:main"
        )
        gui_module, gui_func = self._split_entry(
            self.project.gui_entry_point,
            field="gui_entry_point",
            example="gui.main:main",
            required=False,
        )

        site_dir = self._site_dir(appdir)
        site_dir.mkdir(parents=True, exist_ok=True)

        await self.report(progress, 0.2, "Verificando pip...")
        self.require_tool(
            "pip",
            install_hint="pip debería venir con Python (python3 -m ensurepip).",
        )
        python = sys.executable or "python3"

        if self._has_installable_metadata():
            await self.report(progress, 0.4, "Instalando proyecto con pip...")
            self.check_cancel(cancel_event)
            try:
                await stream_command(
                    [
                        python,
                        "-m",
                        "pip",
                        "install",
                        "--target",
                        str(site_dir),
                        "--upgrade",
                        str(self.project_root),
                    ],
                    cwd=self.project_root,
                    progress=None,
                    stage=self.stage,
                    message="Instalando proyecto con pip...",
                    cancel_event=cancel_event,
                )
            except Exception as e:
                raise self.fail(
                    f"pip install del proyecto falló: {e}",
                    hint="Verifica pyproject.toml/setup.py y la conexión a internet.",
                ) from e
        else:
            await self.report(progress, 0.4, "Sin metadatos de empaquetado: copiando .py...")
            self._copy_sources(site_dir)

        req = self.project_root / "requirements.txt"
        if req.exists():
            await self.report(progress, 0.7, "Instalando requirements.txt...")
            self.check_cancel(cancel_event)
            try:
                await stream_command(
                    [
                        python,
                        "-m",
                        "pip",
                        "install",
                        "--target",
                        str(site_dir),
                        "--upgrade",
                        "-r",
                        str(req),
                    ],
                    cwd=self.project_root,
                    progress=None,
                    stage=self.stage,
                    message="Instalando requirements.txt...",
                    cancel_event=cancel_event,
                )
            except Exception as e:
                raise self.fail(
                    f"pip install de requirements.txt falló: {e}",
                    hint="Verifica los pines de requirements.txt.",
                ) from e

        await self.report(progress, 0.9, "Generando wrapper lanzador...")
        wrapper = self.dest_binary(appdir, self.project.name)
        wrapper.write_text(
            _WRAPPER_TEMPLATE.format(name=self.project.name, module=module, func=func)
        )
        wrapper.chmod(0o755)
        if gui_module is not None and gui_func is not None:
            await self.report(progress, 0.95, "Generando wrapper GUI...")
            gui_wrapper = self.dest_binary(appdir, f"{self.project.name}-gui")
            gui_wrapper.write_text(
                _WRAPPER_TEMPLATE.format(
                    name=f"{self.project.name}-gui", module=gui_module, func=gui_func
                )
            )
            gui_wrapper.chmod(0o755)

        await self.report(progress, 1.0, "Payload Python instalado")
        return wrapper

    def _split_entry(
        self, entry: str, *, field: str, example: str, required: bool = True
    ) -> tuple[str | None, str | None]:
        """Valida `modulo:funcion`. Devuelve (None, None) si vacío y no requerido."""
        entry = (entry or "").strip()
        if not entry:
            if required:
                raise self.fail(
                    f"{field} vacío (formato modulo:funcion).",
                    hint=f"Ejemplo: {field} = '{example}'.",
                )
            return None, None
        if ":" not in entry:
            raise self.fail(
                f"{field} inválido para Python: {entry!r} (formato modulo:funcion).",
                hint=f"Ejemplo: {field} = '{example}'.",
            )
        module, func = (part.strip() for part in entry.split(":", 1))
        if not module or not func:
            raise self.fail(
                f"{field} inválido para Python: {entry!r}.",
                hint=f"Ejemplo: {field} = '{example}'.",
            )
        return module, func

    def _site_dir(self, appdir: Path) -> Path:
        ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        return appdir / "usr/lib" / f"python{ver}" / "site-packages"

    def _has_installable_metadata(self) -> bool:
        root = self.project_root
        return (
            (root / "pyproject.toml").exists()
            or (root / "setup.py").exists()
            or (root / "setup.cfg").exists()
        )

    def _copy_sources(self, site_dir: Path) -> None:
        """Copia paquetes/módulos `.py` sueltos como fallback sin pip."""
        copied = False
        for item in self.project_root.iterdir():
            if item.name.startswith(".") or item.name in {
                "dist",
                "build",
                "__pycache__",
                "tests",
            }:
                continue
            if item.is_dir() and (item / "__init__.py").exists():
                shutil.copytree(item, site_dir / item.name, dirs_exist_ok=True)
                copied = True
            elif item.is_file() and item.suffix == ".py":
                shutil.copy2(item, site_dir / item.name)
                copied = True
        if not copied:
            raise self.fail(
                "No se encontró código Python para empaquetar.",
                hint="Añade pyproject.toml/setup.py o deja módulos .py en la raíz.",
            )
