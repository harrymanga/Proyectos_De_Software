"""Estado compartido del wizard (base para los ViewModels de Fase 5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from appimage_builder.core.constants import Architecture, BuildType, Compression
from appimage_builder.core.models import (
    AppImageBuilderConfig,
    BuildConfig,
    ProjectConfig,
    RuntimeConfig,
)
from appimage_builder.core.services.project_service import detect_project_type


@dataclass
class WizardState:
    """Datos del wizard, sincronizados por las páginas (initialize/validate)."""

    project_path: Path = field(default_factory=Path.cwd)
    build_type: BuildType = BuildType.PYTHON
    entry_point: str = "main:main"
    gui_entry_point: str = ""
    python_version: str = "3.11"

    name: str = "mi-app"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    homepage: str = ""
    icon: str = ""

    architecture: Architecture = Architecture.X86_64
    compression: Compression = Compression.XZ
    output: str = ""
    sign: bool = False
    sign_key: str = ""
    update_information: str = ""
    no_fuse: bool = False
    cache_dir: str = ""
    bundle_tree: bool = False
    linuxdeploy_path: str = ""
    appimagetool_path: str = ""
    # Precargadas desde [tool.appimage-builder] del proyecto (ver detect()).
    # La GUI no las edita: viajan tal cual al build para no perder ajustes CLI.
    excluded_libraries: list[str] = field(default_factory=list)
    prune_paths: list[str] = field(default_factory=list)

    detected_type: BuildType | None = None
    detected_entry: str = ""

    def detect(self) -> None:
        """Auto-detecta el tipo de proyecto desde `project_path`."""
        root = self.project_path.expanduser()
        if root.exists():
            build_type, entry = detect_project_type(root)
            self.detected_type = build_type
            self.detected_entry = entry or ""
            self.build_type = build_type
            if entry:
                self.entry_point = entry
            if not self.name or self.name == "mi-app":
                self.name = root.name
        self._preload_toml(root)

    @staticmethod
    def _read_toml_section(root: Path) -> dict:
        """Lee [tool.appimage-builder] del pyproject vecino ({} si falta/rompe)."""
        try:
            import tomllib
        except ImportError:  # pragma: no cover - py<3.11 no soportado
            return {}
        candidate = root.expanduser() / "pyproject.toml"
        try:
            with candidate.open("rb") as fh:
                data = tomllib.load(fh)
        except (OSError, ValueError):
            return {}
        section = data.get("tool", {}).get("appimage-builder", {})
        return section if isinstance(section, dict) else {}

    def _preload_toml(self, root: Path) -> None:
        """Hereda ajustes previos del TOML que el wizard no edita ni muestra.

        Sin esto, construir desde la GUI pierde `excluded_libraries`
        (ej: Qt5 falla con libQt53DAnimation) aunque estén en el pyproject.
        """
        section = self._read_toml_section(root)
        if not section:
            return
        project = section.get("project", {})
        build = section.get("build", {})
        if isinstance(project, dict):
            if (not self.name or self.name == "mi-app") and project.get("name"):
                self.name = str(project["name"])
            if self.version in {"", "1.0.0"} and project.get("version"):
                self.version = str(project["version"])
            if project.get("entry_point"):
                self.entry_point = str(project["entry_point"])
            if project.get("icon"):
                self.icon = str(project["icon"])
        if isinstance(build, dict):
            excluded = build.get("excluded_libraries", [])
            if isinstance(excluded, list):
                self.excluded_libraries = [str(lib) for lib in excluded if str(lib).strip()]
            pruned = build.get("prune_paths", [])
            if isinstance(pruned, list):
                self.prune_paths = [str(p) for p in pruned if str(p).strip()]

    def output_dir(self) -> Path:
        if self.output.strip():
            return Path(self.output).expanduser()
        return self.project_path.expanduser() / "dist"

    def to_config(self) -> AppImageBuilderConfig:
        """Convierte el estado a la configuración del core (CLI/GUI comparten)."""
        entry = self.entry_point.strip()
        if self.build_type in {BuildType.PYTHON, BuildType.NATIVE} and not entry:
            entry = "main:main"
        project = ProjectConfig(
            name=self.name.strip() or "mi-app",
            version=self.version.strip() or "1.0.0",
            description=self.description.strip(),
            author=self.author.strip(),
            license=self.license.strip() or "MIT",
            homepage=self.homepage.strip(),
            build_type=self.build_type,
            entry_point=entry,
            gui_entry_point=self.gui_entry_point.strip(),
            python_version=self.python_version.strip() or "3.11",
            icon=Path(self.icon).expanduser() if self.icon.strip() else None,
        )
        build = BuildConfig(
            output=self.output_dir(),
            architecture=self.architecture,
            compression=self.compression,
            update_information=self.update_information.strip() or None,
            sign=self.sign,
            sign_key=self.sign_key.strip() or None,
            bundle_tree=self.bundle_tree,
            excluded_libraries=list(self.excluded_libraries),
            prune_paths=list(self.prune_paths),
        )
        runtime = RuntimeConfig(
            no_fuse=self.no_fuse,
            cache_dir=Path(self.cache_dir).expanduser()
            if self.cache_dir.strip()
            else Path.home() / ".cache" / "appimage-builder",
            linuxdeploy_path=Path(self.linuxdeploy_path).expanduser()
            if self.linuxdeploy_path.strip()
            else None,
            appimagetool_path=Path(self.appimagetool_path).expanduser()
            if self.appimagetool_path.strip()
            else None,
        )
        return AppImageBuilderConfig(project=project, build=build, runtime=runtime)
