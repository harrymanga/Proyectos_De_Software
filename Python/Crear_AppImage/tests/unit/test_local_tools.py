"""Tests de herramientas locales (modo sin red)."""

import stat
from pathlib import Path

import pytest

from appimage_builder.core.config import ConfigManager
from appimage_builder.core.exceptions import RuntimeError as ToolRuntimeError
from appimage_builder.core.models import RuntimeConfig
from appimage_builder.runtime.manager import RuntimeManager


def _fake_tool(path: Path, *, executable: bool = True) -> Path:
    path.write_text("#!/bin/bash\nexit 0\n")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


@pytest.mark.unit
async def test_local_paths_skip_download(tmp_path: Path) -> None:
    linuxdeploy = _fake_tool(tmp_path / "linuxdeploy.AppImage")
    appimagetool = _fake_tool(tmp_path / "appimagetool.AppImage")
    manager = RuntimeManager(
        RuntimeConfig(
            cache_dir=tmp_path / "empty-cache",
            linuxdeploy_path=linuxdeploy,
            appimagetool_path=appimagetool,
        )
    )
    seen: list[str] = []

    async def collect(update) -> None:  # type: ignore[no-untyped-def]
        seen.append(update.message)

    tools = await manager.ensure_all(collect)
    assert tools == {"linuxdeploy": linuxdeploy, "appimagetool": appimagetool}
    assert any("local" in message for message in seen)
    assert manager.is_available()


@pytest.mark.unit
async def test_missing_local_path_raises(tmp_path: Path) -> None:
    manager = RuntimeManager(
        RuntimeConfig(
            cache_dir=tmp_path / "cache",
            linuxdeploy_path=tmp_path / "no-existe.AppImage",
        )
    )
    with pytest.raises(ToolRuntimeError, match="no existe"):
        await manager.ensure_linuxdeploy()


@pytest.mark.unit
def test_resolve_prefers_local_over_cache(tmp_path: Path) -> None:
    local = _fake_tool(tmp_path / "local.AppImage")
    manager = RuntimeManager(RuntimeConfig(cache_dir=tmp_path / "cache", linuxdeploy_path=local))
    assert manager.resolve_linuxdeploy() == local
    assert manager.resolve_appimagetool() == manager.appimagetool_path


@pytest.mark.unit
def test_cli_mapping_applies_tool_paths(tmp_path: Path) -> None:
    manager = ConfigManager()
    final = manager.merge(
        cli_settings=manager.load_cli(
            linuxdeploy_path=tmp_path / "ld.AppImage",
            appimagetool_path=tmp_path / "at.AppImage",
        ),
        env_config={},
    )
    assert final.runtime.linuxdeploy_path == (tmp_path / "ld.AppImage").resolve()
    assert final.runtime.appimagetool_path == (tmp_path / "at.AppImage").resolve()


@pytest.mark.unit
def test_vendored_tools_exist_and_run() -> None:
    import subprocess

    tools = Path(__file__).resolve().parent.parent.parent / "tools"
    for name in ("linuxdeploy-x86_64.AppImage", "appimagetool-x86_64.AppImage"):
        target = tools / name
        assert target.exists(), f"falta vendorizado: {name}"
        assert target.stat().st_mode & 0o111
    manager = RuntimeManager(
        RuntimeConfig(
            cache_dir=Path("/tmp/aib-never-created"),
            linuxdeploy_path=tools / "linuxdeploy-x86_64.AppImage",
            appimagetool_path=tools / "appimagetool-x86_64.AppImage",
        )
    )
    assert manager.is_available()
    proc = subprocess.run(
        [str(tools / "appimagetool-x86_64.AppImage"), "--help"],
        capture_output=True,
        text=True,
        timeout=60,
        env={"APPIMAGE_EXTRACT_AND_RUN": "1", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0
    assert "appimagetool" in (proc.stdout + proc.stderr).lower()
