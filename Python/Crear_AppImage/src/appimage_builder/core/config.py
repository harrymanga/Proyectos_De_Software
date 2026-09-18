"""Sistema de configuración jerárquica (TOML + ENV + CLI)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from appimage_builder.core.constants import (
    DEFAULT_CACHE_DIR,
    Architecture,
    BuildType,
    Compression,
)
from appimage_builder.core.exceptions import ConfigurationError
from appimage_builder.core.models import (
    AppImageBuilderConfig,
    BuildConfig,
    ProjectConfig,
    RuntimeConfig,
)


class CLISettings(BaseSettings):
    """Settings provenientes de línea de comandos (alta prioridad)."""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="APPIMAGE_BUILDER_CLI_",
        case_sensitive=False,
    )

    # Project overrides
    project_name: str | None = None
    project_version: str | None = None
    project_description: str | None = None
    project_author: str | None = None
    project_license: str | None = None
    project_homepage: str | None = None
    build_type: BuildType | None = None
    entry_point: str | None = None
    gui_entry_point: str | None = None
    python_version: str | None = None
    python_date: str | None = None
    icon: Path | None = None
    desktop_entry: Path | None = None
    appstream: Path | None = None

    # Build overrides
    output: Path | None = None
    architecture: Architecture | None = None
    compression: Compression | None = None
    update_information: str | None = None
    sign: bool | None = None
    sign_key: str | None = None
    extra_files: list[Path] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    pre_package_hook: Path | None = None
    post_install_hook: Path | None = None
    excluded_libraries: list[str] = Field(default_factory=list)
    bundle_tree: bool | None = None

    # Runtime overrides
    linuxdeploy_version: str | None = None
    appimagetool_version: str | None = None
    python_standalone_date: str | None = None
    cache_dir: Path | None = None
    no_fuse: bool | None = None
    github_token: str | None = None
    linuxdeploy_path: Path | None = None
    appimagetool_path: Path | None = None

    # Global
    config_file: Path | None = None
    verbose: bool = False
    quiet: bool = False
    dry_run: bool = False


class ConfigManager:
    """Gestor de configuración con precedencia: CLI > ENV > TOML > Defaults."""

    def __init__(self) -> None:
        self._cli_settings: CLISettings | None = None
        self._toml_config: AppImageBuilderConfig | None = None
        self._final_config: AppImageBuilderConfig | None = None

    def load_cli(self, **kwargs: Any) -> CLISettings:
        """Carga settings desde CLI kwargs."""
        self._cli_settings = CLISettings(**kwargs)
        return self._cli_settings

    def load_toml(self, path: Path | None = None) -> AppImageBuilderConfig | None:
        """Carga configuración desde pyproject.toml.

        Devuelve None si el archivo no existe o no contiene la sección
        `[tool.appimage-builder]` (no es un error: se usan defaults).
        """
        if path is None:
            path = Path.cwd() / "pyproject.toml"

        if not path.exists():
            return None

        try:
            import tomllib
        except ImportError as e:  # pragma: no cover - Python >= 3.11 siempre
            raise ConfigurationError(
                f"No se pudo leer {path}: falta tomllib.",
                config_path=path,
            ) from e

        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ConfigurationError(
                f"No se pudo cargar la configuración desde {path}",
                config_path=path,
                hint=f"Verifica la sintaxis TOML: {e}",
            ) from e

        if not data.get("tool", {}).get("appimage-builder"):
            return None

        try:
            self._toml_config = AppImageBuilderConfig.from_toml(path)
            return self._toml_config
        except Exception as e:
            raise ConfigurationError(
                f"No se pudo cargar la configuración desde {path}",
                config_path=path,
                hint=f"Verifica la sintaxis TOML: {e}",
            ) from e

    def load_env(self) -> dict[str, Any]:
        """Carga variables de entorno relevantes."""
        env_config: dict[str, Any] = {}

        # Project
        for key in [
            "NAME",
            "VERSION",
            "DESCRIPTION",
            "AUTHOR",
            "LICENSE",
            "HOMEPAGE",
            "BUILD_TYPE",
            "ENTRY_POINT",
            "PYTHON_VERSION",
            "PYTHON_DATE",
        ]:
            env_key = f"APPIMAGE_BUILDER_PROJECT_{key}"
            if env_key in os.environ:
                env_config.setdefault("project", {})[key.lower()] = os.environ[env_key]

        # Build
        for key in [
            "OUTPUT",
            "ARCHITECTURE",
            "COMPRESSION",
            "UPDATE_INFORMATION",
            "SIGN",
            "SIGN_KEY",
            "PRE_PACKAGE_HOOK",
            "POST_INSTALL_HOOK",
        ]:
            env_key = f"APPIMAGE_BUILDER_BUILD_{key}"
            if env_key in os.environ:
                env_config.setdefault("build", {})[key.lower()] = os.environ[env_key]

        # Runtime
        for key in [
            "LINUXDEPLOY_VERSION",
            "APPIMAGETOOL_VERSION",
            "PYTHON_STANDALONE_DATE",
            "CACHE_DIR",
            "NO_FUSE",
            "GITHUB_TOKEN",
        ]:
            env_key = f"APPIMAGE_BUILDER_RUNTIME_{key}"
            if env_key in os.environ:
                env_config.setdefault("runtime", {})[key.lower()] = os.environ[env_key]

        # Extra files and env vars from ENV
        if "APPIMAGE_BUILDER_EXTRA_FILES" in os.environ:
            env_config.setdefault("build", {})["extra_files"] = os.environ[
                "APPIMAGE_BUILDER_EXTRA_FILES"
            ].split(":")

        return env_config

    def merge(
        self,
        toml_config: AppImageBuilderConfig | None = None,
        cli_settings: CLISettings | None = None,
        env_config: dict[str, Any] | None = None,
    ) -> AppImageBuilderConfig:
        """Combina todas las fuentes de configuración con precedencia correcta."""
        # 1. Base: TOML o defaults
        if toml_config is not None:
            base = toml_config.model_copy(deep=True)
        elif self._toml_config is not None:
            base = self._toml_config.model_copy(deep=True)
        else:
            # Configuración por defecto mínima
            base = AppImageBuilderConfig(
                project=ProjectConfig(name="myapp", version="1.0.0", entry_point="main:main"),
                build=BuildConfig(),
                runtime=RuntimeConfig(),
            )

        # 2. Aplicar ENV
        if env_config is not None:
            base = self._apply_env_overrides(base, env_config)

        # 3. Aplicar CLI (máxima prioridad)
        if cli_settings is not None:
            base = self._apply_cli_overrides(base, cli_settings)
        elif self._cli_settings is not None:
            base = self._apply_cli_overrides(base, self._cli_settings)

        self._final_config = base
        return base

    def _apply_env_overrides(
        self, config: AppImageBuilderConfig, env_config: dict[str, Any]
    ) -> AppImageBuilderConfig:
        """Aplica overrides desde variables de entorno."""
        if "project" in env_config:
            for key, value in env_config["project"].items():
                if hasattr(config.project, key):
                    setattr(config.project, key, value)

        if "build" in env_config:
            for key, value in env_config["build"].items():
                if hasattr(config.build, key):
                    # Conversión de tipos básicos
                    if key in {"sign"}:
                        value = value.lower() in ("true", "1", "yes")
                    elif key in {"extra_files"} and isinstance(value, str):
                        value = [Path(p.strip()) for p in value.split(":") if p.strip()]
                    setattr(config.build, key, value)

        if "runtime" in env_config:
            for key, value in env_config["runtime"].items():
                if hasattr(config.runtime, key):
                    if key in {"no_fuse"}:
                        value = value.lower() in ("true", "1", "yes")
                    setattr(config.runtime, key, value)

        return config

    def _apply_cli_overrides(
        self, config: AppImageBuilderConfig, cli: CLISettings
    ) -> AppImageBuilderConfig:
        """Aplica overrides desde CLI (máxima prioridad)."""
        # Project overrides
        project_fields = {
            "project_name": "name",
            "project_version": "version",
            "project_description": "description",
            "project_author": "author",
            "project_license": "license",
            "project_homepage": "homepage",
            "build_type": "build_type",
            "entry_point": "entry_point",
            "gui_entry_point": "gui_entry_point",
            "python_version": "python_version",
            "python_date": "python_date",
            "icon": "icon",
            "desktop_entry": "desktop_entry",
            "appstream": "appstream",
        }
        for cli_attr, model_attr in project_fields.items():
            value = getattr(cli, cli_attr)
            if value is not None:
                setattr(config.project, model_attr, value)

        # Build overrides
        build_fields = {
            "output": "output",
            "architecture": "architecture",
            "compression": "compression",
            "update_information": "update_information",
            "sign": "sign",
            "sign_key": "sign_key",
            "extra_files": "extra_files",
            "env_vars": "env",
            "pre_package_hook": "pre_package_hook",
            "post_install_hook": "post_install_hook",
            "excluded_libraries": "excluded_libraries",
            "bundle_tree": "bundle_tree",
        }
        for cli_attr, model_attr in build_fields.items():
            value = getattr(cli, cli_attr)
            if value is not None and (not isinstance(value, list) or value):
                setattr(config.build, model_attr, value)

        # Runtime overrides
        runtime_fields = {
            "linuxdeploy_version": "linuxdeploy_version",
            "appimagetool_version": "appimagetool_version",
            "python_standalone_date": "python_standalone_date",
            "cache_dir": "cache_dir",
            "no_fuse": "no_fuse",
            "github_token": "github_token",
            "linuxdeploy_path": "linuxdeploy_path",
            "appimagetool_path": "appimagetool_path",
        }
        for cli_attr, model_attr in runtime_fields.items():
            value = getattr(cli, cli_attr)
            if value is not None:
                setattr(config.runtime, model_attr, value)

        return config

    def get_final_config(self) -> AppImageBuilderConfig:
        """Retorna la configuración final fusionada."""
        if self._final_config is None:
            self.merge()
        return self._final_config

    def save_toml(self, path: Path) -> None:
        """Guarda la configuración actual como TOML."""
        if self._final_config is None:
            raise ConfigurationError("No hay configuración final para guardar")
        self._final_config.to_toml(path)


def create_default_config(project_path: Path) -> AppImageBuilderConfig:
    """Crea una configuración por defecto detectando el proyecto."""
    from appimage_builder.core.services.project_service import detect_project_type

    project_type, detected_entry = detect_project_type(project_path)

    from appimage_builder.core.constants import BuildType as _BuildType

    if detected_entry:
        entry_point = detected_entry
    elif project_type in {_BuildType.PYTHON, _BuildType.NATIVE}:
        entry_point = "main:main"
    else:
        entry_point = ""

    return AppImageBuilderConfig(
        project=ProjectConfig(
            name=project_path.name,
            version="1.0.0",
            build_type=project_type,
            entry_point=entry_point,
        ),
        build=BuildConfig(output=project_path / "dist"),
        runtime=RuntimeConfig(cache_dir=DEFAULT_CACHE_DIR),
    )
