"""Tests de detección de proyectos."""

from pathlib import Path

import pytest

from appimage_builder.core.constants import BuildType
from appimage_builder.core.services.project_service import detect_project_type


@pytest.mark.unit
def test_detect_python(sample_python_project: Path) -> None:
    build_type, entry = detect_project_type(sample_python_project)
    assert build_type == BuildType.PYTHON
    assert entry == "main:main"


@pytest.mark.unit
def test_detect_make_uses_output_flag(sample_c_project: Path) -> None:
    build_type, entry = detect_project_type(sample_c_project)
    assert build_type == BuildType.NATIVE
    assert entry == "hello"


@pytest.mark.unit
def test_detect_generic_binary(sample_generic_project: Path) -> None:
    build_type, entry = detect_project_type(sample_generic_project)
    assert build_type == BuildType.GENERIC
    assert entry == "mybin"


@pytest.mark.unit
def test_detect_empty_dir_falls_back_to_generic(tmp_path: Path) -> None:
    build_type, _ = detect_project_type(tmp_path)
    assert build_type == BuildType.GENERIC
