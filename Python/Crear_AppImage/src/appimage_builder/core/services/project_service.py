"""Servicios de negocio puros - Project Detection Service."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from appimage_builder.core.constants import BuildType


def detect_project_type(project_path: Path) -> tuple[BuildType, str | None]:
    """
    Detecta automáticamente el tipo de proyecto y entry point sugerido.

    Returns:
        Tupla (BuildType, entry_point_sugerido)
    """
    project_path = project_path.resolve()

    # Verificar archivos indicadores en orden de prioridad
    detectors = [
        (_detect_python, BuildType.PYTHON),
        (_detect_rust, BuildType.NATIVE),
        (_detect_go, BuildType.NATIVE),
        (_detect_cmake, BuildType.NATIVE),
        (_detect_meson, BuildType.NATIVE),
        (_detect_make, BuildType.NATIVE),
        (_detect_cargo_toml, BuildType.NATIVE),
        (_detect_pyproject, BuildType.PYTHON),
        (_detect_setup_py, BuildType.PYTHON),
        (_detect_requirements, BuildType.PYTHON),
        (_detect_binary, BuildType.GENERIC),
    ]

    for detector, build_type in detectors:
        entry_point = detector(project_path)
        if entry_point is not None:
            return build_type, entry_point

    # Fallback: genérico
    return BuildType.GENERIC, None


def _detect_python(project_path: Path) -> str | None:
    """Detecta proyecto Python y su entry point."""
    # pyproject.toml con [project.scripts]
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            with pyproject.open("rb") as f:
                data = tomllib.load(f)

            # [project.scripts]
            scripts = data.get("project", {}).get("scripts", {})
            if scripts:
                # Tomar el primer script
                first_script = next(iter(scripts.values()))
                if isinstance(first_script, str) and ":" in first_script:
                    return first_script

            # [tool.poetry.scripts]
            poetry_scripts = data.get("tool", {}).get("poetry", {}).get("scripts", {})
            if poetry_scripts:
                first_script = next(iter(poetry_scripts.values()))
                if isinstance(first_script, str) and ":" in first_script:
                    return first_script

            # [tool.flit.scripts]
            flit_scripts = data.get("tool", {}).get("flit", {}).get("scripts", {})
            if flit_scripts:
                first_script = next(iter(flit_scripts.values()))
                if isinstance(first_script, str) and ":" in first_script:
                    return first_script
        except Exception:
            pass

    # setup.py con entry_points
    setup_py = project_path / "setup.py"
    if setup_py.exists():
        try:
            # Intentar extraer entry_points del setup.py
            result = subprocess.run(
                [sys.executable, setup_py, "--entry-points"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Parsear salida (formato: name = module:function)
                for line in result.stdout.strip().split("\n"):
                    if "=" in line:
                        _, entry = line.split("=", 1)
                        entry = entry.strip()
                        if ":" in entry:
                            return entry
        except Exception:
            pass

    # setup.cfg
    setup_cfg = project_path / "setup.cfg"
    if setup_cfg.exists():
        try:
            import configparser

            parser = configparser.ConfigParser()
            parser.read(setup_cfg)
            if parser.has_section("options.entry_points"):
                for _, value in parser.items("options.entry_points"):
                    if ":" in value:
                        return value.strip()
        except Exception:
            pass

    return None


def _detect_rust(project_path: Path) -> str | None:
    """Detecta proyecto Rust (Cargo.toml)."""
    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.exists():
        try:
            import tomllib

            with cargo_toml.open("rb") as f:
                data = tomllib.load(f)

            # [[bin]] sections
            bins = data.get("bin", [])
            if bins:
                return bins[0].get("name", "") or data.get("package", {}).get("name", "")

            # package.name como fallback
            pkg_name = data.get("package", {}).get("name")
            if pkg_name:
                return pkg_name.replace("-", "_")
        except Exception:
            pass
    return None


def _detect_cargo_toml(project_path: Path) -> str | None:
    """Alias para Rust."""
    return _detect_rust(project_path)


def _detect_go(project_path: Path) -> str | None:
    """Detecta proyecto Go (go.mod)."""
    go_mod = project_path / "go.mod"
    if go_mod.exists():
        try:
            content = go_mod.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("module "):
                    module_path = line[7:].strip()
                    return module_path.split("/")[-1]
        except Exception:
            pass
    return None


def _detect_cmake(project_path: Path) -> str | None:
    """Detecta proyecto CMake."""
    cmake_lists = project_path / "CMakeLists.txt"
    if cmake_lists.exists():
        try:
            content = cmake_lists.read_text()
            # Buscar add_executable o project()
            import re

            # add_executable(target ...)
            match = re.search(r"add_executable\s*\(\s*(\w+)", content, re.IGNORECASE)
            if match:
                return match.group(1)

            # project(name ...)
            match = re.search(r"project\s*\(\s*(\w+)", content, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        except Exception:
            pass
    return None


def _detect_meson(project_path: Path) -> str | None:
    """Detecta proyecto Meson."""
    meson_build = project_path / "meson.build"
    if meson_build.exists():
        try:
            content = meson_build.read_text()
            import re

            # executable('name', ...)
            match = re.search(r"executable\s*\(\s*['\"](\w+)['\"]", content)
            if match:
                return match.group(1)

            # project('name', ...)
            match = re.search(r"project\s*\(\s*['\"](\w+)['\"]", content)
            if match:
                return match.group(1).lower()
        except Exception:
            pass
    return None


def _detect_make(project_path: Path) -> str | None:
    """Detecta proyecto Makefile."""
    makefile = project_path / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text()
            import re

            # Buscar target principal o variable BIN/TARGET
            for pattern in [
                r"^(?:BIN|TARGET|EXEC|PROGRAM)\s*[:=]\s*(\S+)",
                r"^all:\s*([A-Za-z0-9_.-]+)\s*$",
            ]:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).split()[0]
            # Fallback: salida de compilación en la receta (-o <binario>)
            match = re.search(r"-o\s+([A-Za-z0-9_.-]+)", content)
            if match:
                return match.group(1)
        except Exception:
            pass
    return None


def _detect_pyproject(project_path: Path) -> str | None:
    """Detecta pyproject.toml genérico."""
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        return "main:main"  # Fallback genérico
    return None


def _detect_setup_py(project_path: Path) -> str | None:
    """Detecta setup.py genérico."""
    setup_py = project_path / "setup.py"
    if setup_py.exists():
        return "main:main"
    return None


def _detect_requirements(project_path: Path) -> str | None:
    """Detecta requirements.txt."""
    for req_file in ["requirements.txt", "requirements.pip", "requirements-dev.txt"]:
        if (project_path / req_file).exists():
            return "main:main"
    return None


def _detect_binary(project_path: Path) -> str | None:
    """Detecta binario ejecutable suelto."""
    for item in project_path.iterdir():
        if item.is_file() and item.stat().st_mode & 0o111:  # Ejecutable
            # Excluir archivos comunes que no son la app principal
            if item.name not in {
                "configure",
                "install.sh",
                "build.sh",
                "run.sh",
                "test.sh",
                "Makefile",
                "cmake",
                "meson",
                "ninja",
            } and item.suffix not in {".desktop", ".png", ".svg", ".txt", ".md"}:
                return item.name
    return None


def find_project_root(start_path: Path | None = None) -> Path:
    """Encuentra la raíz del proyecto buscando archivos indicadores."""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    markers = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Cargo.toml",
        "go.mod",
        "CMakeLists.txt",
        "meson.build",
        "Makefile",
        ".git",
    ]

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    return start_path.resolve()
