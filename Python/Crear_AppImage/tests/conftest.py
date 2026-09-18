"""Fixtures compartidas: proyectos ejemplo, tools fake, Qt offscreen."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def sample_python_project(tmp_path: Path) -> Path:
    # En subdir propio: el AppDir del test no debe contaminar el proyecto.
    root = tmp_path / "proj"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=61"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "demopy"\nversion = "0.1.0"\n'
    )
    pkg = root / "demomod"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('def main():\n    print("hola")\n    return 0\n')
    return root


@pytest.fixture
def sample_c_project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "hello.c").write_text(
        '#include <stdio.h>\nint main(void){printf("native-ok\\n");return 0;}\n'
    )
    (root / "Makefile").write_text("all:\n\tgcc -o hello hello.c\n")
    return root


@pytest.fixture
def sample_generic_project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    binary = root / "mybin"
    binary.write_text("#!/bin/bash\necho generic-ok\n")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return root


@pytest.fixture
def fake_tools_cache(tmp_path: Path) -> Path:
    """Cache con linuxdeploy/appimagetool falsos (sin red)."""
    tools = tmp_path / "cache" / "tools"
    tools.mkdir(parents=True)
    linuxdeploy = tools / "linuxdeploy-x86_64.AppImage"
    linuxdeploy.write_text("#!/bin/bash\nexit 0\n")
    appimagetool = tools / "appimagetool-x86_64.AppImage"
    appimagetool.write_text('#!/bin/bash\ntouch "${@: -1}"\nexit 0\n')
    for tool in (linuxdeploy, appimagetool):
        tool.chmod(tool.stat().st_mode | stat.S_IXUSR)
    return tmp_path / "cache"


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
