"""Builder nativo: compila (cargo/go/cmake/meson/make) y copia el binario."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import tomllib
from pathlib import Path

from appimage_builder.builders.base import BaseBuilder, ProgressCb
from appimage_builder.bundler.tools import stream_command


class NativeBuilder(BaseBuilder):
    """Detecta el sistema de build, compila y deja el binario en `usr/bin`."""

    async def install(
        self,
        *,
        appdir: Path,
        progress: ProgressCb = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path | None:
        system = self.detect_system()
        await self.report(progress, 0.1, f"Sistema de build detectado: {system}...")
        built = await self._compile(system, progress, cancel_event)
        dest = self.dest_binary(appdir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, dest)
        dest.chmod(0o755)
        await self.report(progress, 1.0, f"Binario instalado: {dest.name}")
        return dest

    def detect_system(self) -> str:
        root = self.project_root
        if (root / "Cargo.toml").exists():
            return "cargo"
        if (root / "go.mod").exists():
            return "go"
        if (root / "CMakeLists.txt").exists():
            return "cmake"
        if (root / "meson.build").exists():
            return "meson"
        if (root / "Makefile").exists() or (root / "makefile").exists():
            return "make"
        raise self.fail(
            "No se detectó sistema de build (Cargo.toml, go.mod, CMakeLists.txt, "
            "meson.build o Makefile).",
            hint="Usa build_type = 'generic' si ya tienes el binario compilado.",
        )

    async def _compile(
        self,
        system: str,
        progress: ProgressCb,
        cancel_event: asyncio.Event | None,
    ) -> Path:
        handler = {
            "cargo": self._build_cargo,
            "go": self._build_go,
            "cmake": self._build_cmake,
            "meson": self._build_meson,
            "make": self._build_make,
        }[system]
        return await handler(progress, cancel_event)

    def _expected_binary_name(self) -> str:
        if self.project.entry_point:
            return self.project.entry_point
        if (self.project_root / "Cargo.toml").exists():
            try:
                data = tomllib.loads((self.project_root / "Cargo.toml").read_text())
                bins = data.get("bin", [])
                if bins and bins[0].get("name"):
                    return str(bins[0]["name"])
                pkg = data.get("package", {}).get("name")
                if pkg:
                    return str(pkg).replace("-", "_")
            except (OSError, tomllib.TOMLDecodeError):
                pass
        return self.project.name

    async def _build_cargo(self, progress: ProgressCb, cancel_event: asyncio.Event | None) -> Path:
        self.require_tool("cargo", install_hint="Instala Rust (https://rustup.rs).")
        await self.report(progress, 0.3, "Compilando con cargo...")
        self.check_cancel(cancel_event)
        await stream_command(
            ["cargo", "build", "--release"],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Compilando con cargo...",
            cancel_event=cancel_event,
        )
        candidate = self.project_root / "target/release" / self._expected_binary_name()
        if candidate.exists():
            return candidate
        found = self._newest_executable(self.project_root / "target/release")
        if found is None:
            raise self.fail("cargo terminó pero no se encontró el binario en target/release.")
        return found

    async def _build_go(self, progress: ProgressCb, cancel_event: asyncio.Event | None) -> Path:
        self.require_tool("go", install_hint="Instala Go (https://go.dev/dl).")
        await self.report(progress, 0.3, "Compilando con go...")
        self.check_cancel(cancel_event)
        out = Path(tempfile.mkdtemp(prefix="aib-go-")) / self._expected_binary_name()
        await stream_command(
            ["go", "build", "-o", str(out), "."],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Compilando con go...",
            cancel_event=cancel_event,
        )
        if not out.exists():
            raise self.fail("go build terminó pero no generó el binario.")
        return out

    async def _build_cmake(self, progress: ProgressCb, cancel_event: asyncio.Event | None) -> Path:
        self.require_tool("cmake", install_hint="Instala cmake y un compilador (gcc/clang).")
        build_dir = Path(tempfile.mkdtemp(prefix="aib-cmake-"))
        await self.report(progress, 0.3, "Configurando con cmake...")
        self.check_cancel(cancel_event)
        await stream_command(
            [
                "cmake",
                "-S",
                str(self.project_root),
                "-B",
                str(build_dir),
                "-DCMAKE_BUILD_TYPE=Release",
            ],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Configurando con cmake...",
            cancel_event=cancel_event,
        )
        await self.report(progress, 0.6, "Compilando con cmake...")
        await stream_command(
            ["cmake", "--build", str(build_dir), "--config", "Release"],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Compilando con cmake...",
            cancel_event=cancel_event,
        )
        return self._locate_built_binary(build_dir)

    async def _build_meson(self, progress: ProgressCb, cancel_event: asyncio.Event | None) -> Path:
        self.require_tool("meson", install_hint="Instala meson y ninja (pip install meson ninja).")
        self.require_tool("ninja", install_hint="Instala ninja.")
        build_dir = Path(tempfile.mkdtemp(prefix="aib-meson-"))
        await self.report(progress, 0.3, "Configurando con meson...")
        self.check_cancel(cancel_event)
        await stream_command(
            ["meson", "setup", str(build_dir), str(self.project_root)],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Configurando con meson...",
            cancel_event=cancel_event,
        )
        await self.report(progress, 0.6, "Compilando con ninja...")
        await stream_command(
            ["ninja", "-C", str(build_dir)],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Compilando con ninja...",
            cancel_event=cancel_event,
        )
        return self._locate_built_binary(build_dir)

    async def _build_make(self, progress: ProgressCb, cancel_event: asyncio.Event | None) -> Path:
        self.require_tool("make", install_hint="Instala make y un compilador (gcc).")
        await self.report(progress, 0.3, "Compilando con make...")
        self.check_cancel(cancel_event)
        jobs = os.cpu_count() or 2
        await stream_command(
            ["make", f"-j{jobs}"],
            cwd=self.project_root,
            progress=None,
            stage=self.stage,
            message="Compilando con make...",
            cancel_event=cancel_event,
        )
        return self._locate_built_binary(self.project_root)

    def _locate_built_binary(self, search_dir: Path) -> Path:
        expected = search_dir / self._expected_binary_name()
        if expected.is_file():
            return expected
        found = self._newest_executable(search_dir)
        if found is None:
            raise self.fail(
                f"La compilación terminó pero no se encontró {self._expected_binary_name()}.",
                hint="Define entry_point con el nombre exacto del binario.",
            )
        return found

    @staticmethod
    def _newest_executable(directory: Path) -> Path | None:
        """El ejecutable regular más reciente (ignora objetos/librerías)."""
        best: Path | None = None
        best_mtime = -1.0
        skip_suffixes = {".o", ".a", ".so", ".c", ".h", ".cmake", ".txt", ".ninja", ".build"}
        skip_names = {"CMakeCache.txt", "Makefile", "build.ninja", "cmake_install.cmake"}
        try:
            entries = list(directory.iterdir())
        except OSError:
            return None
        for item in entries:
            if not item.is_file() or item.is_symlink():
                continue
            if item.name in skip_names or item.suffix in skip_suffixes:
                continue
            if not item.stat().st_mode & 0o111:
                continue
            mtime = item.stat().st_mtime
            if mtime > best_mtime:
                best, best_mtime = item, mtime
        return best
