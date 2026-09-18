"""Tests de ConfigManager (precedencia CLI > ENV > TOML > defaults)."""

from pathlib import Path

import pytest

from appimage_builder.core.config import ConfigManager
from appimage_builder.core.exceptions import ConfigurationError


@pytest.mark.unit
def test_merge_defaults_has_entry_point() -> None:
    config = ConfigManager().merge()
    assert config.project.name == "myapp"
    assert config.project.entry_point == "main:main"


@pytest.mark.unit
def test_load_toml_missing_section_returns_none(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text('[project]\nname = "ajeno"\n')
    assert ConfigManager().load_toml(target) is None


@pytest.mark.unit
def test_load_toml_invalid_section_raises(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text('[tool.appimage-builder]\nproject = { name = "x" }\n')
    with pytest.raises(ConfigurationError):
        ConfigManager().load_toml(target)


@pytest.mark.unit
def test_cli_overrides_win(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text(
        '[tool.appimage-builder.project]\nname = "toml-name"\nversion = "1.0.0"\n'
        'entry_point = "main:main"\n'
    )
    manager = ConfigManager()
    toml_config = manager.load_toml(target)
    cli = manager.load_cli(project_name="cli-name")
    final = manager.merge(toml_config=toml_config, cli_settings=cli, env_config={})
    assert final.project.name == "cli-name"


@pytest.mark.unit
def test_env_overrides_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text(
        '[tool.appimage-builder.project]\nname = "toml-name"\nversion = "1.0.0"\n'
        'entry_point = "main:main"\n'
    )
    monkeypatch.setenv("APPIMAGE_BUILDER_PROJECT_NAME", "env-name")
    manager = ConfigManager()
    toml_config = manager.load_toml(target)
    final = manager.merge(toml_config=toml_config, env_config=manager.load_env())
    assert final.project.name == "env-name"
