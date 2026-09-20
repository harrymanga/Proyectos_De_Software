"""Tests de prune_paths (poda pre-linuxdeploy)."""

from pathlib import Path

import pytest

from appimage_builder.bundler.tools import prune_appdir
from appimage_builder.core.config import ConfigManager
from appimage_builder.core.models import BuildConfig
from appimage_builder.gui.state import WizardState


@pytest.mark.unit
def test_build_config_prune_paths_default_empty() -> None:
    assert BuildConfig().prune_paths == []


@pytest.mark.unit
def test_cli_mapping_applies_prune_paths() -> None:
    manager = ConfigManager()
    final = manager.merge(
        cli_settings=manager.load_cli(
            prune_paths=["usr/lib/python3*/site-packages/PyQt5/Qt5/qml"]
        ),
        env_config={},
    )
    assert final.build.prune_paths == ["usr/lib/python3*/site-packages/PyQt5/Qt5/qml"]


@pytest.mark.unit
def test_cli_mapping_skips_empty_prune_paths() -> None:
    manager = ConfigManager()
    final = manager.merge(cli_settings=manager.load_cli(prune_paths=[]), env_config={})
    assert final.build.prune_paths == []


@pytest.mark.unit
def test_prune_appdir_removes_files_and_dirs(tmp_path) -> None:
    appdir = tmp_path / "AppDir"
    (appdir / "usr" / "lib" / "qml" / "sub").mkdir(parents=True)
    (appdir / "usr" / "lib" / "qml" / "sub" / "a.so").write_text("x")
    (appdir / "usr" / "bin" / "app").parent.mkdir(parents=True)
    (appdir / "usr" / "bin" / "app").write_text("x")
    removed = prune_appdir(appdir, ["usr/lib/qml"])
    assert removed == {"files": 0, "dirs": 1}
    assert not (appdir / "usr" / "lib" / "qml").exists()
    assert (appdir / "usr" / "bin" / "app").exists()


@pytest.mark.unit
def test_prune_appdir_ignores_outside_and_empty(tmp_path) -> None:
    appdir = tmp_path / "AppDir"
    appdir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep")
    removed = prune_appdir(appdir, ["", ".", "../outside.txt", "nomatch*"])
    assert removed == {"files": 0, "dirs": 0}
    assert outside.exists()


TOML_PRUNE = """\
[tool.appimage-builder.project]
name = "Demo"
version = "1.0.0"
build_type = "python"
entry_point = "main:main"

[tool.appimage-builder.build]
prune_paths = ["usr/lib/python3*/site-packages/PyQt5/Qt5/qml"]
"""


@pytest.mark.unit
def test_detect_preloads_prune_paths(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(TOML_PRUNE, encoding="utf-8")
    (tmp_path / "main.py").write_text("def main(): ...\n", encoding="utf-8")
    state = WizardState(project_path=tmp_path)
    state.detect()
    assert state.prune_paths == ["usr/lib/python3*/site-packages/PyQt5/Qt5/qml"]
    assert state.to_config().build.prune_paths == [
        "usr/lib/python3*/site-packages/PyQt5/Qt5/qml"
    ]
