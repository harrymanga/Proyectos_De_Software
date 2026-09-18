"""Core: lógica de negocio pura compartida entre CLI y GUI."""

from appimage_builder.core.constants import (
    Architecture,
    BuildStage,
    BuildType,
    Compression,
    ExitCode,
    coerce_architecture,
    coerce_compression,
)
from appimage_builder.core.exceptions import (
    AppImageBuilderError,
    BuildError,
    CancellationError,
    ConfigurationError,
    DependencyError,
    DownloadError,
    ProjectDetectionError,
    RuntimeError,
    SigningError,
    ValidationError,
)
from appimage_builder.core.models import (
    AppImageBuilderConfig,
    BuildConfig,
    BuildProgress,
    ProjectConfig,
    RuntimeConfig,
    ValidationResult,
)

__all__ = [
    "AppImageBuilderConfig",
    "AppImageBuilderError",
    "Architecture",
    "BuildConfig",
    "BuildError",
    "BuildProgress",
    "BuildStage",
    "BuildType",
    "CancellationError",
    "Compression",
    "ConfigurationError",
    "DependencyError",
    "DownloadError",
    "ExitCode",
    "ProjectConfig",
    "ProjectDetectionError",
    "RuntimeConfig",
    "RuntimeError",
    "SigningError",
    "ValidationError",
    "ValidationResult",
    "coerce_architecture",
    "coerce_compression",
]
