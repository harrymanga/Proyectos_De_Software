"""Tests de validadores compartidos."""

from pathlib import Path

import pytest

from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import (
    AppImageBuilderConfig,
    BuildConfig,
    ProjectConfig,
    ValidationResult,
)
from appimage_builder.core.services.template_service import TemplateService
from appimage_builder.validators import (
    validate_appdir,
    validate_desktop_file,
    validate_metainfo_file,
    validate_project_config,
)


def _good_appdir(base: Path) -> Path:
    appdir = base / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    apprun = appdir / "AppRun"
    apprun.write_text("#!/bin/bash\necho hi\n")
    apprun.chmod(0o755)
    project = ProjectConfig(
        name="demo", version="1.0.0", build_type=BuildType.GENERIC, entry_point="demo"
    )
    (appdir / "demo.desktop").write_text(
        TemplateService().generate_desktop_entry(project, BuildConfig())
    )
    (appdir / "demo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    metainfo_dir = appdir / "usr/share/metainfo"
    metainfo_dir.mkdir(parents=True)
    (metainfo_dir / "demo.metainfo.xml").write_text(
        TemplateService().generate_appstream(project, BuildConfig())
    )
    return appdir


@pytest.mark.unit
def test_appdir_good(tmp_path: Path) -> None:
    result = validate_appdir(_good_appdir(tmp_path))
    assert result.valid, result.errors


@pytest.mark.unit
def test_appdir_missing_everything(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = validate_appdir(empty)
    assert not result.valid
    assert len(result.errors) >= 2


@pytest.mark.unit
def test_desktop_missing_exec_warns(tmp_path: Path) -> None:
    target = tmp_path / "x.desktop"
    target.write_text("[Desktop Entry]\nType=Application\nName=x\nIcon=x\n")
    result = validate_desktop_file(target)
    assert any("Exec" in warning for warning in result.warnings)


@pytest.mark.unit
def test_desktop_missing_header_errors(tmp_path: Path) -> None:
    target = tmp_path / "x.desktop"
    target.write_text("Name=x\n")
    assert not validate_desktop_file(target).valid


@pytest.mark.unit
def test_metainfo_generated_is_valid(tmp_path: Path) -> None:
    project = ProjectConfig(name="demo", version="1.0.0", build_type=BuildType.GENERIC)
    target = tmp_path / "demo.metainfo.xml"
    target.write_text(TemplateService().generate_appstream(project, BuildConfig()))
    assert validate_metainfo_file(target).valid


@pytest.mark.unit
def test_metainfo_broken_xml_errors(tmp_path: Path) -> None:
    target = tmp_path / "bad.metainfo.xml"
    target.write_text("<component><oops>")
    assert not validate_metainfo_file(target).valid


@pytest.mark.unit
def test_project_config_validator() -> None:
    config = AppImageBuilderConfig(
        project=ProjectConfig(name="demo", version="1.0.0", entry_point="main:main")
    )
    assert validate_project_config(config).valid
    assert isinstance(validate_project_config(config, ValidationResult(valid=True)).info, list)
