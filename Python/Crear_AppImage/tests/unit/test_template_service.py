"""Tests de plantillas AppRun/.desktop/AppStream."""

import pytest

from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import BuildConfig, ProjectConfig
from appimage_builder.core.services.template_service import TemplateService


@pytest.mark.unit
def test_launch_binary_python_uses_project_name() -> None:
    project = ProjectConfig(
        name="mi-app", version="1.0.0", build_type=BuildType.PYTHON, entry_point="main:main"
    )
    assert TemplateService.launch_binary(project) == "mi-app"


@pytest.mark.unit
def test_launch_binary_native_uses_entry_point() -> None:
    project = ProjectConfig(
        name="mi-app", version="1.0.0", build_type=BuildType.NATIVE, entry_point="mi-bin"
    )
    assert TemplateService.launch_binary(project) == "mi-bin"


@pytest.mark.unit
def test_apprun_python_has_no_module_syntax() -> None:
    service = TemplateService()
    project = ProjectConfig(
        name="mi-app", version="1.0.0", build_type=BuildType.PYTHON, entry_point="main:main"
    )
    content = service.generate_apprun(project, BuildConfig())
    assert "usr/bin/mi-app" in content
    assert "main:main" not in content
    assert "$APPDIR" in content  # variables shell intactas


@pytest.mark.unit
def test_desktop_exec_matches_launch_binary() -> None:
    service = TemplateService()
    project = ProjectConfig(
        name="mi-app", version="1.0.0", build_type=BuildType.PYTHON, entry_point="main:main"
    )
    assert "Exec=mi-app" in service.generate_desktop_entry(project, BuildConfig())
