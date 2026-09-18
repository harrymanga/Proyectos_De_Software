"""Constructor de la estructura AppDir estándar."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from appimage_builder.core.exceptions import BuildError
from appimage_builder.core.models import BuildConfig, ProjectConfig

if TYPE_CHECKING:
    from appimage_builder.core.services.template_service import TemplateService

_HICOLOR_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


class AppDirBuilder:
    """Crea y puebla un AppDir a partir de la configuración.

    Estructura generada::

        AppDir/
          AppRun
          <name>.desktop
          <name>.png (si hay icono)
          usr/bin/
          usr/lib/
          usr/share/applications/<name>.desktop -> ../../../<name>.desktop
          usr/share/icons/hicolor/<size>x<size>/apps/<name>.png
          usr/share/metainfo/<name>.metainfo.xml
    """

    def __init__(
        self,
        project: ProjectConfig,
        build: BuildConfig,
        appdir: Path,
        templates: TemplateService | None = None,
    ) -> None:
        from appimage_builder.core.services.template_service import TemplateService

        self.project = project
        self.build = build
        self.appdir = appdir
        self.templates = templates or TemplateService()

    def build_base(self) -> dict[str, Path]:
        """Crea la estructura base y devuelve las rutas generadas."""
        self._create_dirs()
        apprun = self.write_apprun()
        desktop = self.write_desktop_entry()
        metainfo = self.write_appstream()
        icon_paths = self.copy_icon()
        self.copy_extra_files()
        self.run_hook(self.build.pre_package_hook, "pre-package")
        return {
            "apprun": apprun,
            "desktop": desktop,
            "metainfo": metainfo,
            **{f"icon_{i}": p for i, p in enumerate(icon_paths)},
        }

    def _create_dirs(self) -> None:
        for sub in (
            "usr/bin",
            "usr/lib",
            "usr/share/applications",
            "usr/share/metainfo",
        ):
            (self.appdir / sub).mkdir(parents=True, exist_ok=True)
        for size in _HICOLOR_SIZES:
            (self.appdir / "usr/share/icons/hicolor" / f"{size}x{size}" / "apps").mkdir(
                parents=True, exist_ok=True
            )

    def write_apprun(self) -> Path:
        dest = self.appdir / "AppRun"
        self.templates.write_apprun(self.project, self.build, dest)
        return dest

    def write_desktop_entry(self) -> Path:
        desktop_name = f"{self.project.name}.desktop"
        dest = self.appdir / desktop_name
        self.templates.write_desktop_entry(self.project, self.build, dest)
        link = self.appdir / "usr/share/applications" / desktop_name
        try:
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(f"../../../{desktop_name}")
        except OSError as e:
            raise BuildError(
                f"No se pudo crear el symlink del .desktop: {e}",
                stage="preparing",
                hint="Verifica permisos de escritura en el AppDir.",
            ) from e
        return dest

    def write_appstream(self) -> Path:
        dest = self.appdir / "usr/share/metainfo" / f"{self.project.name}.metainfo.xml"
        self.templates.write_appstream(self.project, self.build, dest)
        return dest

    def copy_icon(self) -> list[Path]:
        """Copia el icono a la raíz y a hicolor. Devuelve destinos escritos.

        Sin icono configurado genera un placeholder (linuxdeploy exige Icon).
        """
        if not self.project.icon:
            src: Path | None = None
        else:
            candidate = self.project.icon.expanduser()
            if not candidate.exists():
                raise BuildError(
                    f"Icono no encontrado: {candidate}",
                    stage="preparing",
                    hint="Verifica la ruta del icono en la configuración.",
                )
            src = candidate
        if src is None:
            src = self._write_placeholder_icon()
        icon_name = f"{self.project.name}{src.suffix or '.png'}"
        written: list[Path] = []
        root_dest = self.appdir / icon_name
        if src.resolve() != root_dest.resolve():
            shutil.copy2(src, root_dest)
            written.append(root_dest)
        else:
            written.append(root_dest)
        for size in _HICOLOR_SIZES:
            dest = self.appdir / "usr/share/icons/hicolor" / f"{size}x{size}" / "apps" / icon_name
            shutil.copy2(src, dest)
            written.append(dest)
        return written

    def _write_placeholder_icon(self) -> Path:
        """Genera un PNG sólido de 64px (solo stdlib) como icono temporal."""
        import struct
        import zlib

        size = 64
        rgb = (47, 126, 216)
        raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))

        def chunk(kind: bytes, data: bytes) -> bytes:
            out = struct.pack(">I", len(data)) + kind + data
            return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b"")
        )
        dest = self.appdir / f"{self.project.name}.png"
        dest.write_bytes(png)
        return dest

    def copy_extra_files(self) -> list[Path]:
        """Copia `extra_files` dentro del AppDir (preservando nombres)."""
        written: list[Path] = []
        for src in self.build.extra_files:
            src_path = src.expanduser()
            if not src_path.exists():
                raise BuildError(
                    f"Archivo extra no encontrado: {src_path}",
                    stage="preparing",
                    hint="Verifica `build.extra_files` en la configuración.",
                )
            if src_path.is_dir():
                dest = self.appdir / "usr/share" / src_path.name
                shutil.copytree(src_path, dest, dirs_exist_ok=True)
            else:
                dest = self.appdir / "usr/bin" / src_path.name
                shutil.copy2(src_path, dest)
            written.append(dest)
        return written

    def run_hook(self, hook: Path | None, name: str) -> None:
        """Ejecuta un hook de shell con APPDIR en el entorno."""
        if hook is None:
            return
        from appimage_builder.utils.hooks import run_hook_script

        run_hook_script(
            hook,
            name=name,
            stage="preparing",
            cwd=self.appdir,
            extra_env={"APPDIR": str(self.appdir)},
        )
