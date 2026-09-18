"""Factoría de builders por tipo de proyecto."""

from __future__ import annotations

from pathlib import Path

from appimage_builder.builders.base import BaseBuilder
from appimage_builder.builders.generic_builder import GenericBuilder
from appimage_builder.builders.native_builder import NativeBuilder
from appimage_builder.builders.python_builder import PythonBuilder
from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import BuildConfig, ProjectConfig


def get_builder(
    build_type: BuildType,
    *,
    project: ProjectConfig,
    build: BuildConfig,
    project_root: Path,
) -> BaseBuilder:
    """Devuelve el builder adecuado para el tipo de proyecto."""
    if build_type == BuildType.PYTHON:
        return PythonBuilder(project, build, project_root)
    if build_type == BuildType.NATIVE:
        return NativeBuilder(project, build, project_root)
    return GenericBuilder(project, build, project_root)
