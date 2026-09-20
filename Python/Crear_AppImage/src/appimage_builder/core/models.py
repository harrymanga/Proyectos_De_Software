"""Modelos de datos principales usando Pydantic."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from appimage_builder.core.constants import (
    Architecture,
    BuildType,
    Compression,
)


class ProjectConfig(BaseModel):
    """Configuración del proyecto a empaquetar."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
            pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$",
            description="Nombre del proyecto (alfanumérico, guiones, puntos, guiones bajos)",
        ),
    ]
    version: Annotated[
        str,
        Field(
            pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9._-]+)?(\+[a-zA-Z0-9._-]+)?$",
            description="Versión semántica (ej: 1.0.0, 2.1.0-beta.1)",
        ),
    ]
    description: Annotated[str, Field(default="", max_length=500)]
    author: Annotated[str, Field(default="", max_length=200)]
    license: Annotated[str, Field(default="MIT", max_length=100)]
    homepage: Annotated[str, Field(default="", max_length=500)]

    build_type: Annotated[BuildType, Field(default=BuildType.PYTHON)]
    entry_point: Annotated[str, Field(default="", max_length=200)]
    gui_entry_point: Annotated[
        str,
        Field(
            default="",
            max_length=200,
            description="Entry GUI opcional (Python: modulo:funcion, nativo: binario). "
            "Habilita `AppRun --gui` y el lanzador <nombre>-gui.",
        ),
    ]

    # Python-specific
    python_version: Annotated[str, Field(default="3.11", pattern=r"^\d+\.\d+$")]
    python_date: Annotated[str | None, Field(default=None, pattern=r"^\d{8}$")]

    # Assets
    icon: Annotated[Path | None, Field(default=None)]
    desktop_entry: Annotated[Path | None, Field(default=None)]
    appstream: Annotated[Path | None, Field(default=None)]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v.lower() in {"appimage", "appdir", "apprun", "usr", "bin", "lib"}:
            raise ValueError(f"'{v}' es un nombre reservado del sistema AppImage")
        return v

    @field_validator("icon", "desktop_entry", "appstream", mode="before")
    @classmethod
    def resolve_paths(cls, v: str | Path | None) -> Path | None:
        if v is None or v == "":
            return None
        return Path(v).expanduser().resolve()

    @model_validator(mode="after")
    def validate_entry_point(self) -> Self:
        if self.build_type == BuildType.PYTHON and not self.entry_point:
            raise ValueError(
                "entry_point es requerido para proyectos Python (formato: modulo:funcion)"
            )
        if self.build_type == BuildType.NATIVE and not self.entry_point:
            raise ValueError("entry_point es requerido para proyectos nativos (nombre del binario)")
        return self


class BuildConfig(BaseModel):
    """Configuración del proceso de build."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    output: Annotated[Path, Field(default_factory=lambda: Path.cwd() / "dist")]
    architecture: Annotated[Architecture, Field(default=Architecture.X86_64)]
    compression: Annotated[Compression, Field(default=Compression.XZ)]
    update_information: Annotated[str | None, Field(default=None, max_length=500)]
    sign: Annotated[bool, Field(default=False)]
    sign_key: Annotated[str | None, Field(default=None, max_length=100)]
    extra_files: Annotated[list[Path], Field(default_factory=list)]
    env: Annotated[dict[str, str], Field(default_factory=dict)]
    pre_package_hook: Annotated[Path | None, Field(default=None)]
    post_install_hook: Annotated[Path | None, Field(default=None)]
    excluded_libraries: Annotated[
        list[str], Field(default_factory=list, description="Librerías a excluir en linuxdeploy")
    ]
    prune_paths: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Rutas (glob, relativas al AppDir) a podar antes de linuxdeploy",
        ),
    ]
    bundle_tree: Annotated[
        bool,
        Field(
            default=False,
            description="Genérico: copia todo el árbol al AppDir y crea shim en usr/bin.",
        ),
    ]

    @field_validator(
        "output", "extra_files", "pre_package_hook", "post_install_hook", mode="before"
    )
    @classmethod
    def resolve_paths(cls, v: Any) -> Any:
        if isinstance(v, (str, Path)):
            return Path(v).expanduser().resolve()
        if isinstance(v, list):
            return [Path(p).expanduser().resolve() for p in v]
        return v

    @field_validator("update_information")
    @classmethod
    def validate_update_info(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith(("gh-releases-", "zsync|")):
            raise ValueError(
                "update_information debe empezar con 'gh-releases-' o 'zsync|' "
                "(ver especificación AppImage)"
            )
        return v


class RuntimeConfig(BaseModel):
    """Configuración de runtimes y herramientas."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    linuxdeploy_version: Annotated[str, Field(default="latest")]
    appimagetool_version: Annotated[str, Field(default="latest")]
    python_standalone_date: Annotated[str | None, Field(default=None, pattern=r"^\d{8}$")]
    cache_dir: Annotated[
        Path, Field(default_factory=lambda: Path.home() / ".cache" / "appimage-builder")
    ]
    no_fuse: Annotated[bool, Field(default=False)]
    github_token: Annotated[str | None, Field(default=None, max_length=200)]
    linuxdeploy_path: Annotated[
        Path | None, Field(default=None, description="Binario local (no descarga).")
    ]
    appimagetool_path: Annotated[
        Path | None, Field(default=None, description="Binario local (no descarga).")
    ]

    @field_validator("cache_dir", mode="before")
    @classmethod
    def resolve_cache_dir(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()

    @field_validator("linuxdeploy_path", "appimagetool_path", mode="before")
    @classmethod
    def resolve_tool_paths(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        return Path(v).expanduser().resolve() if isinstance(v, (str, Path)) else v


class AppImageBuilderConfig(BaseModel):
    """Configuración completa de la aplicación."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    project: ProjectConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    @classmethod
    def from_toml(cls, path: Path) -> Self:
        import tomllib

        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data.get("tool", {}).get("appimage-builder", {}))

    def to_toml(self, path: Path) -> None:
        import tomli_w

        data = {"tool": {"appimage-builder": self.model_dump(mode="json")}}
        with path.open("wb") as f:
            tomli_w.dump(data, f)


class BuildProgress(BaseModel):
    """Progreso del build para reporting."""

    model_config = ConfigDict(frozen=True)

    stage: str
    progress: Annotated[float, Field(ge=0.0, le=1.0)]
    message: str
    details: str = ""


class ValidationResult(BaseModel):
    """Resultado de validación."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    info: list[str] = Field(default_factory=list)

    def add_error(self, error: str) -> ValidationResult:
        return ValidationResult(
            valid=False,
            errors=[*self.errors, error],
            warnings=self.warnings,
            info=self.info,
        )

    def add_warning(self, warning: str) -> ValidationResult:
        return ValidationResult(
            valid=self.valid,
            errors=self.errors,
            warnings=[*self.warnings, warning],
            info=self.info,
        )

    def add_info(self, info: str) -> ValidationResult:
        return ValidationResult(
            valid=self.valid,
            errors=self.errors,
            warnings=self.warnings,
            info=[*self.info, info],
        )
