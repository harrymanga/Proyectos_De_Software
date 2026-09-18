"""Tests del RuntimeManager (sin red)."""

from pathlib import Path

import pytest

from appimage_builder.core.constants import Architecture
from appimage_builder.core.models import RuntimeConfig
from appimage_builder.runtime.downloader import download_file
from appimage_builder.runtime.manager import RuntimeManager


@pytest.mark.unit
def test_tool_urls_include_arch(tmp_path: Path) -> None:
    manager = RuntimeManager(RuntimeConfig(cache_dir=tmp_path), Architecture.AARCH64)
    assert "aarch64" in manager.linuxdeploy_url()
    assert "aarch64" in manager.appimagetool_url()


@pytest.mark.unit
def test_empty_cache_is_not_available(tmp_path: Path) -> None:
    manager = RuntimeManager(RuntimeConfig(cache_dir=tmp_path))
    assert not manager.is_available()


@pytest.mark.unit
def test_fake_tools_cache_is_available(fake_tools_cache: Path) -> None:
    manager = RuntimeManager(RuntimeConfig(cache_dir=fake_tools_cache))
    assert manager.is_available()
    assert manager.is_linuxdeploy_available()
    assert manager.is_appimagetool_available()


@pytest.mark.unit
def test_clear_cache(fake_tools_cache: Path) -> None:
    manager = RuntimeManager(RuntimeConfig(cache_dir=fake_tools_cache))
    manager.clear_cache()
    assert not manager.is_available()


@pytest.mark.unit
async def test_download_reuses_existing_file(tmp_path: Path) -> None:
    dest = tmp_path / "cached.bin"
    dest.write_bytes(b"x" * 16)
    result = await download_file("https://example.invalid/file", dest)
    assert result == dest.resolve()
