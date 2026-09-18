"""Tests de builders (genérico/nativo rápidos; Python con red = slow)."""

import shutil
import subprocess
from pathlib import Path

import pytest

from appimage_builder.builders.factory import get_builder
from appimage_builder.builders.generic_builder import GenericBuilder
from appimage_builder.builders.native_builder import NativeBuilder
from appimage_builder.builders.python_builder import PythonBuilder
from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import BuildConfig, ProjectConfig


@pytest.mark.unit
async def test_generic_builder_copies_binary(tmp_path: Path, sample_generic_project: Path) -> None:
    project = ProjectConfig(
        name="genapp", version="1.0.0", build_type=BuildType.GENERIC, entry_point="mybin"
    )
    build = BuildConfig(output=tmp_path / "dist")
    appdir = tmp_path / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    dest = await GenericBuilder(project, build, sample_generic_project).install(appdir=appdir)
    assert dest is not None and dest.exists()
    assert dest.stat().st_mode & 0o111


@pytest.mark.unit
async def test_generic_builder_bundle_tree(tmp_path: Path) -> None:
    import subprocess

    root = tmp_path / "proj"
    root.mkdir()
    (root / "data.txt").write_text("payload-data\n")
    launcher = root / "run.sh"
    launcher.write_text('#!/bin/bash\ncd "${0%/*}"\ncat data.txt\n')
    launcher.chmod(0o755)
    project = ProjectConfig(
        name="treeapp", version="1.0.0", build_type=BuildType.GENERIC, entry_point="run.sh"
    )
    build = BuildConfig(output=tmp_path / "dist", bundle_tree=True)
    appdir = tmp_path / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    dest = await GenericBuilder(project, build, root).install(appdir=appdir)
    assert dest is not None and dest.name == "run.sh"
    assert (appdir / "run.sh").exists() and (appdir / "data.txt").exists()
    env = {"APPDIR": str(appdir), "PATH": "/usr/bin:/bin"}
    out = subprocess.run([str(dest)], capture_output=True, text=True, env=env, check=True)
    assert out.stdout.strip() == "payload-data"


@pytest.mark.unit
async def test_generic_builder_tree_skips_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "dist").mkdir()
    (root / "dist" / "old.AppImage").write_bytes(b"x")
    (root / "build").mkdir()
    (root / "run.sh").write_text("#!/bin/bash\necho hi\n")
    (root / "run.sh").chmod(0o755)
    project = ProjectConfig(
        name="treeapp", version="1.0.0", build_type=BuildType.GENERIC, entry_point="run.sh"
    )
    build = BuildConfig(output=tmp_path / "dist", bundle_tree=True)
    appdir = tmp_path / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    await GenericBuilder(project, build, root).install(appdir=appdir)
    assert (appdir / "run.sh").exists()
    assert not (appdir / "dist").exists()
    assert not (appdir / "build").exists()


@pytest.mark.unit
async def test_native_builder_make(tmp_path: Path, sample_c_project: Path) -> None:
    if shutil.which("make") is None or shutil.which("gcc") is None:
        pytest.skip("make/gcc no disponibles")
    project = ProjectConfig(
        name="helloapp", version="1.0.0", build_type=BuildType.NATIVE, entry_point="hello"
    )
    build = BuildConfig(output=tmp_path / "dist")
    appdir = tmp_path / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    dest = await NativeBuilder(project, build, sample_c_project).install(appdir=appdir)
    assert dest is not None and dest.exists()
    out = subprocess.run([str(dest)], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "native-ok"


@pytest.mark.unit
def test_factory_returns_matching_builder(tmp_path: Path) -> None:
    project = ProjectConfig(name="x", version="1.0.0", build_type=BuildType.GENERIC)
    build = BuildConfig(output=tmp_path)
    assert isinstance(
        get_builder(BuildType.PYTHON, project=project, build=build, project_root=tmp_path),
        PythonBuilder,
    )
    assert isinstance(
        get_builder(BuildType.NATIVE, project=project, build=build, project_root=tmp_path),
        NativeBuilder,
    )
    assert isinstance(
        get_builder(BuildType.GENERIC, project=project, build=build, project_root=tmp_path),
        GenericBuilder,
    )


@pytest.mark.slow
@pytest.mark.unit
async def test_python_builder_pip_install(tmp_path: Path, sample_python_project: Path) -> None:
    project = ProjectConfig(
        name="demopy", version="1.0.0", build_type=BuildType.PYTHON, entry_point="demomod:main"
    )
    build = BuildConfig(output=tmp_path / "dist")
    appdir = tmp_path / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    dest = await PythonBuilder(project, build, sample_python_project).install(appdir=appdir)
    assert dest is not None and dest.exists()
    assert dest.stat().st_mode & 0o111
