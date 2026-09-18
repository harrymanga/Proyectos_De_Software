"""E2E del BuildService con herramientas falsas (sin red)."""

from pathlib import Path

import pytest

from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import BuildConfig, ProjectConfig, RuntimeConfig
from appimage_builder.core.services.build_service import BuildService


@pytest.mark.integration
async def test_build_generic_end_to_end(
    tmp_path: Path, sample_generic_project: Path, fake_tools_cache: Path
) -> None:
    project = ProjectConfig(
        name="genapp", version="1.0.0", build_type=BuildType.GENERIC, entry_point="mybin"
    )
    build = BuildConfig(output=tmp_path / "dist")
    runtime = RuntimeConfig(cache_dir=fake_tools_cache)
    service = BuildService(
        project=project, build=build, project_root=sample_generic_project, runtime=runtime
    )
    try:
        stages: set[str] = set()

        async def collect(update) -> None:  # type: ignore[no-untyped-def]
            stages.add(update.stage)

        output = await service.build(progress_callback=collect)
        assert output.exists()
        assert (service.appdir / "AppRun").exists()
        assert (service.appdir / "genapp.desktop").exists()
        assert (service.appdir / "usr/bin/mybin").exists()
        assert {"preparing", "downloading_runtime", "creating_appimage"} <= stages
    finally:
        service.cleanup()
