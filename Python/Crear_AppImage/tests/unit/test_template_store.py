"""Tests del almacén de plantillas."""

from pathlib import Path

import pytest

from appimage_builder.core.exceptions import ConfigurationError
from appimage_builder.core.models import AppImageBuilderConfig, BuildConfig, ProjectConfig
from appimage_builder.core.services.template_store import TemplateStore


def _config() -> AppImageBuilderConfig:
    return AppImageBuilderConfig(
        project=ProjectConfig(name="demo", version="1.0.0", entry_point="main:main"),
        build=BuildConfig(),
    )


@pytest.mark.unit
def test_store_roundtrip(tmp_path: Path) -> None:
    store = TemplateStore(tmp_path / "templates")
    dest = store.save("demo-tpl", _config())
    assert dest.exists()
    assert store.list_names() == ["demo-tpl"]
    loaded = store.load("demo-tpl")
    assert loaded.project.name == "demo"


@pytest.mark.unit
def test_store_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        TemplateStore(tmp_path).save("mal nombre!", _config())


@pytest.mark.unit
def test_store_missing_load_and_delete(tmp_path: Path) -> None:
    store = TemplateStore(tmp_path)
    with pytest.raises(ConfigurationError):
        store.load("nope")
    with pytest.raises(ConfigurationError):
        store.delete("nope")
