"""Constantes y enumeraciones centrales del proyecto."""

from enum import Enum
from pathlib import Path


class BuildType(str, Enum):
    """Tipo de proyecto a empaquetar."""

    PYTHON = "python"
    NATIVE = "native"
    GENERIC = "generic"

    @property
    def display_name(self) -> str:
        return {
            BuildType.PYTHON: "Aplicación Python",
            BuildType.NATIVE: "Aplicación Nativa (C/C++/Rust/Go)",
            BuildType.GENERIC: "Binario Genérico",
        }[self]

    @property
    def description(self) -> str:
        return {
            BuildType.PYTHON: "Proyecto con pyproject.toml, setup.py o requirements.txt",
            BuildType.NATIVE: "Proyecto compilado con CMake, Cargo, Make, etc.",
            BuildType.GENERIC: "Ejecutable precompilado o binario suelto",
        }[self]


class Architecture(str, Enum):
    """Arquitecturas soportadas."""

    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    I686 = "i686"
    ARMHF = "armhf"

    @property
    def display_name(self) -> str:
        return {
            Architecture.X86_64: "x86_64 (64-bit Intel/AMD)",
            Architecture.AARCH64: "ARM64 (Apple Silicon, Raspberry Pi 4+)",
            Architecture.I686: "i686 (32-bit Intel/AMD)",
            Architecture.ARMHF: "ARMhf (32-bit ARM)",
        }[self]

    @property
    def linuxdeploy_arch(self) -> str:
        return {
            Architecture.X86_64: "x86_64",
            Architecture.AARCH64: "aarch64",
            Architecture.I686: "i686",
            Architecture.ARMHF: "armhf",
        }[self]

    @property
    def appimagetool_arch(self) -> str:
        return {
            Architecture.X86_64: "x86_64",
            Architecture.AARCH64: "aarch64",
            Architecture.I686: "i686",
            Architecture.ARMHF: "armhf",
        }[self]

    @property
    def python_standalone_arch(self) -> str:
        return {
            Architecture.X86_64: "x86_64",
            Architecture.AARCH64: "aarch64",
            Architecture.I686: "i686",
            Architecture.ARMHF: "armhf",
        }[self]


class Compression(str, Enum):
    """Algoritmos de compresión SquashFS."""

    XZ = "xz"
    GZIP = "gzip"
    ZSTD = "zstd"
    LZO = "lzo"

    @property
    def mksquashfs_flag(self) -> str:
        return {
            Compression.XZ: "-comp xz",
            Compression.GZIP: "-comp gzip",
            Compression.ZSTD: "-comp zstd",
            Compression.LZO: "-comp lzo",
        }[self]

    @property
    def description(self) -> str:
        return {
            Compression.XZ: "Mejor ratio, más lento (recomendado)",
            Compression.GZIP: "Rápido, ratio medio",
            Compression.ZSTD: "Muy rápido, buen ratio",
            Compression.LZO: "Más rápido, ratio bajo",
        }[self]


class BuildStage(str, Enum):
    """Etapas del proceso de build."""

    PREPARING = "preparing"
    DOWNLOADING_RUNTIME = "downloading_runtime"
    INSTALLING_DEPS = "installing_deps"
    RUNNING_LINUXDEPLOY = "running_linuxdeploy"
    CREATING_APPIMAGE = "creating_appimage"
    SIGNING = "signing"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def display_name(self) -> str:
        return {
            BuildStage.PREPARING: "Preparando AppDir",
            BuildStage.DOWNLOADING_RUNTIME: "Descargando runtimes",
            BuildStage.INSTALLING_DEPS: "Instalando dependencias",
            BuildStage.RUNNING_LINUXDEPLOY: "Ejecutando linuxdeploy",
            BuildStage.CREATING_APPIMAGE: "Creando AppImage",
            BuildStage.SIGNING: "Firmando / Generando zsync",
            BuildStage.COMPLETED: "Completado",
            BuildStage.FAILED: "Fallido",
        }[self]

    @property
    def icon(self) -> str:
        return {
            BuildStage.PREPARING: "📁",
            BuildStage.DOWNLOADING_RUNTIME: "⬇️",
            BuildStage.INSTALLING_DEPS: "📦",
            BuildStage.RUNNING_LINUXDEPLOY: "🔧",
            BuildStage.CREATING_APPIMAGE: "📦",
            BuildStage.SIGNING: "🔐",
            BuildStage.COMPLETED: "✅",
            BuildStage.FAILED: "❌",
        }[self]


class ExitCode(int, Enum):
    """Códigos de salida POSIX estándar."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_USAGE = 2
    PERMISSION_DENIED = 77
    COMMAND_NOT_FOUND = 127
    CANCELLED = 130
    CONFIG_ERROR = 78
    BUILD_ERROR = 79
    VALIDATION_ERROR = 80
    RUNTIME_ERROR = 81


def coerce_architecture(value: Architecture | str) -> Architecture:
    """Convierte a `Architecture` (Qt stringifica los str-Enum en userData)."""
    if isinstance(value, Architecture):
        return value
    try:
        return Architecture(str(value))
    except ValueError:
        return Architecture.X86_64


def coerce_compression(value: Compression | str) -> Compression:
    """Convierte a `Compression` (Qt stringifica los str-Enum en userData)."""
    if isinstance(value, Compression):
        return value
    try:
        return Compression(str(value))
    except ValueError:
        return Compression.XZ


# Rutas y URLs por defecto
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "appimage-builder"
DEFAULT_OUTPUT_DIR = Path.cwd() / "dist"

# GitHub Releases URLs
LINUXDEPLOY_RELEASE_URL = "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-{arch}.AppImage"
APPIMAGETOOL_RELEASE_URL = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-{arch}.AppImage"
PYTHON_STANDALONE_API_URL = (
    "https://api.github.com/repos/astral-sh/python-build-standalone/releases"
)

# Nombres de archivos esperados en AppDir
APPDIR_REQUIRED_FILES = ["AppRun", "*.desktop", "*.png", "*.svg"]
APPDIR_EXECUTABLE_NAME = "AppRun"

# Extensiones de archivo
DESKTOP_EXTENSION = ".desktop"
APPIMAGE_EXTENSION = ".AppImage"
ZSYNC_EXTENSION = ".zsync"
GPG_EXTENSION = ".sig"

# Variables de entorno especiales
ENV_APPIMAGE_BUILDER_CONFIG = "APPIMAGE_BUILDER_CONFIG"
ENV_APPIMAGE_BUILDER_CACHE = "APPIMAGE_BUILDER_CACHE"
ENV_APPIMAGE_BUILDER_NO_FUSE = "APPIMAGE_BUILDER_NO_FUSE"
ENV_APPIMAGE_BUILDER_DEBUG = "APPIMAGE_BUILDER_DEBUG"
