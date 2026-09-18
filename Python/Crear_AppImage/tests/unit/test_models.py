"""Tests de modelos Pydantic."""

import pytest
from pydantic import ValidationError

from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import (
    AppImageBuilderConfig,
    BuildConfig,
    ProjectConfig,
    RuntimeConfig,
)


@pytest.mark.unit
def test_project_config_valid() -> None:
    config = ProjectConfig(name="demo", version="1.0.0", entry_point="main:main")
    assert config.build_type == BuildType.PYTHON


@pytest.mark.unit
def test_project_config_reserved_name() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(name="usr", version="1.0.0", entry_point="main:main")


@pytest.mark.unit
def test_project_config_bad_version() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(name="demo", version="nope", entry_point="main:main")


@pytest.mark.unit
def test_project_config_python_requires_entry() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(name="demo", version="1.0.0", build_type=BuildType.PYTHON)


@pytest.mark.unit
def test_project_config_generic_allows_empty_entry() -> None:
    config = ProjectConfig(name="demo", version="1.0.0", build_type=BuildType.GENERIC)
    assert config.entry_point == ""


@pytest.mark.unit
def test_build_config_update_info() -> None:
    BuildConfig(update_information="gh-releases-u/r")
    with pytest.raises(ValidationError):
        BuildConfig(update_information="bogus")


@pytest.mark.unit
def test_full_config_defaults() -> None:
    config = AppImageBuilderConfig(
        project=ProjectConfig(name="demo", version="1.0.0", entry_point="main:main")
    )
    assert isinstance(config.build, BuildConfig)
    assert isinstance(config.runtime, RuntimeConfig)
