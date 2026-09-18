"""Tests de excluded_libraries (Fase deploy)."""

import pytest

from appimage_builder.core.config import ConfigManager
from appimage_builder.core.models import BuildConfig


@pytest.mark.unit
def test_build_config_excluded_libraries_default_empty() -> None:
    assert BuildConfig().excluded_libraries == []


@pytest.mark.unit
def test_cli_mapping_applies_excludes() -> None:
    manager = ConfigManager()
    final = manager.merge(
        cli_settings=manager.load_cli(excluded_libraries=["libpq.so.5"]),
        env_config={},
    )
    assert final.build.excluded_libraries == ["libpq.so.5"]


@pytest.mark.unit
def test_cli_mapping_skips_empty_excludes() -> None:
    manager = ConfigManager()
    final = manager.merge(cli_settings=manager.load_cli(excluded_libraries=[]), env_config={})
    assert final.build.excluded_libraries == []
