"""Tests del runner de hooks compartido."""

from pathlib import Path

import pytest

from appimage_builder.core.exceptions import BuildError
from appimage_builder.utils.hooks import run_hook_script


@pytest.mark.unit
def test_hook_ok_with_env(tmp_path: Path) -> None:
    hook = tmp_path / "ok.sh"
    hook.write_text("#!/bin/bash\necho marker-$MYVAR > result.txt\n")
    run_hook_script(hook, name="test", stage="preparing", cwd=tmp_path, extra_env={"MYVAR": "42"})
    assert (tmp_path / "result.txt").read_text().strip() == "marker-42"


@pytest.mark.unit
def test_hook_failure_reports_exit_and_output(tmp_path: Path) -> None:
    hook = tmp_path / "fail.sh"
    hook.write_text("#!/bin/bash\necho boom >&2\nexit 3\n")
    with pytest.raises(BuildError, match="exit 3"):
        run_hook_script(hook, name="test", stage="preparing", cwd=tmp_path)


@pytest.mark.unit
def test_hook_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="no encontrado"):
        run_hook_script(tmp_path / "missing.sh", name="test", stage="preparing", cwd=tmp_path)


@pytest.mark.unit
def test_appdir_pre_package_hook_runs(tmp_path: Path) -> None:
    from appimage_builder.bundler.appdir import AppDirBuilder
    from appimage_builder.core.constants import BuildType
    from appimage_builder.core.models import BuildConfig, ProjectConfig

    hook = tmp_path / "pre.sh"
    hook.write_text('#!/bin/bash\ntouch "$APPDIR/pre-hook-ran"\n')
    project = ProjectConfig(
        name="hookapp", version="1.0.0", build_type=BuildType.GENERIC, entry_point="run"
    )
    build = BuildConfig(output=tmp_path / "dist", pre_package_hook=hook)
    appdir = tmp_path / "AppDir"
    AppDirBuilder(project=project, build=build, appdir=appdir).build_base()
    assert (appdir / "pre-hook-ran").exists()
