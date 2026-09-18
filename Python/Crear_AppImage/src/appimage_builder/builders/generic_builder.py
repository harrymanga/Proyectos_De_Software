"""Builder genérico: copia un binario precompilado a `usr/bin`."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from appimage_builder.builders.base import BaseBuilder, ProgressCb

_SKIP_NAMES = {
    "configure",
    "install.sh",
    "build.sh",
    "run.sh",
    "test.sh",
    "Makefile",
    "makefile",
    "cmake",
    "meson",
    "ninja",
}


class GenericBuilder(BaseBuilder):
    """Localiza el ejecutable y lo copia al AppDir.

    Con `build.bundle_tree`, copia todo el árbol del proyecto a la raíz del
    AppDir (apps portables con datos/ELFs relativos) y deja un shim en
    `usr/bin/<entry>` que re-ejecuta el script en su ubicación real (así los
    `cd $0-dir` del lanzador siguen funcionando).
    """

    async def install(
        self,
        *,
        appdir: Path,
        progress: ProgressCb = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path | None:
        await self.report(progress, 0.3, "Localizando binario precompilado...")
        self.check_cancel(cancel_event)
        src = self._resolve_binary()
        if self.build.bundle_tree:
            return await self._install_tree(appdir, src, progress, cancel_event)
        dest = self.dest_binary(appdir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        dest.chmod(0o755)
        await self.report(progress, 1.0, f"Binario copiado: {dest.name}")
        return dest

    async def _install_tree(
        self,
        appdir: Path,
        src: Path,
        progress: ProgressCb,
        cancel_event: asyncio.Event | None,
    ) -> Path:
        """Copia el árbol completo + shim lanzador. Devuelve el shim."""
        await self.report(progress, 0.4, "Copiando árbol del proyecto al AppDir...")
        self.check_cancel(cancel_event)
        root = self.project_root.resolve()
        try:
            rel = src.resolve().relative_to(root)
        except ValueError:
            raise self.fail(
                f"El binario {src} está fuera del proyecto: bundle_tree lo exige dentro.",
                hint="Usa entry_point con una ruta dentro del proyecto.",
            ) from None
        await asyncio.to_thread(self._copy_tree, root, appdir)
        self.check_cancel(cancel_event)
        # Shim en usr/bin/<nombre> que re-ejecuta el script real con $0 correcto.
        shim_name = Path(self.project.entry_point.strip() or self.project.name).name
        shim = appdir / "usr/bin" / shim_name
        shim.parent.mkdir(parents=True, exist_ok=True)
        shim.write_text(f'#!/bin/bash\nexec "$APPDIR/{rel.as_posix()}" "$@"\n')
        shim.chmod(0o755)
        await self.report(progress, 1.0, f"Árbol copiado + shim: {shim.name}")
        return shim

    def _copy_tree(self, root: Path, appdir: Path) -> None:
        """Mezcla el árbol en el AppDir sin pisar AppRun/.desktop/icono propios."""
        reserved = {
            "AppRun",
            f"{self.project.name}.desktop",
            f"{self.project.name}.png",
            f"{self.project.name}.svg",
        }
        # Artefactos de salida/compilación nunca se empaquetan (evita que un
        # dist/ dentro del proyecto se auto-incluya en el siguiente build).
        skipped_dirs = {"dist", "build", "__pycache__"}
        for item in root.iterdir():
            if item.name.startswith(".") or item.name in reserved:
                continue
            if item.suffix in {".AppImage", ".egg-info"}:
                continue  # nunca empaquetar AppImages ni metadata de build
            if item.is_dir() and item.name in skipped_dirs:
                continue
            dest = appdir / item.name
            if item.is_symlink():
                if dest.is_symlink() or dest.exists():
                    dest.unlink()
                dest.symlink_to(item.readlink())
            elif item.is_dir():
                shutil.copytree(item, dest, symlinks=True, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    def _resolve_binary(self) -> Path:
        # 1. entry_point como ruta (absoluta o relativa al proyecto).
        entry = self.project.entry_point.strip()
        if entry:
            candidates = [
                Path(entry).expanduser(),
                self.project_root / entry,
            ]
            for candidate in candidates:
                if candidate.is_file():
                    return candidate
            # 2. entry_point como nombre de ejecutable en la raíz.
            named = self._find_named(entry)
            if named is not None:
                return named
        # 3. Nombre del proyecto como ejecutable.
        named = self._find_named(self.project.name)
        if named is not None:
            return named
        # 4. Primer ejecutable suelto (heurística).
        fallback = self._find_any_executable()
        if fallback is not None:
            return fallback
        raise self.fail(
            "No se encontró ningún binario precompilado en el proyecto.",
            hint="Define entry_point con la ruta o nombre del ejecutable.",
        )

    def _find_named(self, name: str) -> Path | None:
        if not name or "/" in name or "\\" in name:
            return None
        candidate = self.project_root / name
        if candidate.is_file() and candidate.stat().st_mode & 0o111:
            return candidate
        return None

    def _find_any_executable(self) -> Path | None:
        try:
            entries = sorted(self.project_root.iterdir())
        except OSError:
            return None
        for item in entries:
            if not item.is_file() or item.name in _SKIP_NAMES:
                continue
            if item.suffix in {
                ".py",
                ".c",
                ".h",
                ".o",
                ".a",
                ".so",
                ".toml",
                ".cfg",
                ".txt",
                ".md",
                ".desktop",
                ".png",
                ".svg",
            }:
                continue
            if item.stat().st_mode & 0o111:
                return item
        return None
