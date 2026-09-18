"""ViewModel del wizard: estado observable + validación centralizada."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from appimage_builder.core.constants import Architecture, BuildType, Compression
from appimage_builder.core.models import AppImageBuilderConfig
from appimage_builder.gui.state import WizardState

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9._-]+)?(\+[a-zA-Z0-9._-]+)?$")
_RESERVED_NAMES = {"appimage", "appdir", "apprun", "usr", "bin", "lib"}


class WizardViewModel(QObject):
    """Envuelve `WizardState` con señales y validadores por paso.

    Las páginas leen `state` y mutan vía setters (emiten `state_changed`);
    `validate_*` devuelven listas de errores (vacía = válido).
    """

    state_changed = Signal()
    detection_finished = Signal()
    validation_changed = Signal(list)

    def __init__(self, state: WizardState | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.state = state or WizardState()
        self._last_errors: list[str] = []

    # --- mutadores (emiten state_changed) ---

    def set_project_path(self, path: Path | str) -> None:
        self.state.project_path = Path(path).expanduser()
        self.state_changed.emit()

    def detect(self) -> None:
        self.state.detect()
        self.detection_finished.emit()
        self.state_changed.emit()

    def set_build_type(self, build_type: BuildType) -> None:
        self.state.build_type = build_type
        self.state_changed.emit()

    def set_entry_point(self, entry: str) -> None:
        self.state.entry_point = entry.strip()
        self.state_changed.emit()

    def set_gui_entry_point(self, entry: str) -> None:
        self.state.gui_entry_point = entry.strip()
        self.state_changed.emit()

    def set_python_version(self, version: str) -> None:
        self.state.python_version = version.strip()
        self.state_changed.emit()

    def set_metadata(
        self,
        *,
        name: str,
        version: str,
        description: str,
        author: str,
        license: str,
        homepage: str,
        icon: str,
    ) -> None:
        self.state.name = name.strip()
        self.state.version = version.strip()
        self.state.description = description.strip()
        self.state.author = author.strip()
        self.state.license = license.strip()
        self.state.homepage = homepage.strip()
        self.state.icon = icon.strip()
        self.state_changed.emit()

    def set_advanced(
        self,
        *,
        architecture: Architecture | str,
        compression: Compression | str,
        output: str,
        sign: bool,
        sign_key: str,
        update_information: str,
        no_fuse: bool,
        cache_dir: str = "",
        bundle_tree: bool = False,
        linuxdeploy_path: str = "",
        appimagetool_path: str = "",
    ) -> None:
        from appimage_builder.core.constants import coerce_architecture, coerce_compression

        self.state.architecture = coerce_architecture(architecture)
        self.state.compression = coerce_compression(compression)
        self.state.output = output.strip()
        self.state.sign = sign
        self.state.sign_key = sign_key.strip()
        self.state.update_information = update_information.strip()
        self.state.no_fuse = no_fuse
        self.state.cache_dir = cache_dir.strip()
        self.state.bundle_tree = bundle_tree
        self.state.linuxdeploy_path = linuxdeploy_path.strip()
        self.state.appimagetool_path = appimagetool_path.strip()
        self.state_changed.emit()

    # --- validación por paso ---

    def validate_project(self) -> list[str]:
        errors = []
        if not self.state.project_path.expanduser().exists():
            errors.append(f"No existe el proyecto: {self.state.project_path}")
        return self._store(errors)

    def validate_type(self) -> list[str]:
        errors = []
        if self.state.build_type in {BuildType.PYTHON, BuildType.NATIVE}:
            if not self.state.entry_point.strip():
                errors.append("El entry point es obligatorio para este tipo de proyecto.")
            elif self.state.build_type == BuildType.PYTHON and ":" not in self.state.entry_point:
                errors.append("Entry point Python con formato modulo:funcion (ej: main:main).")
        return self._store(errors)

    def validate_specific(self) -> list[str]:
        errors = []
        if self.state.build_type == BuildType.PYTHON:
            if not self.state.entry_point.strip() or ":" not in self.state.entry_point:
                errors.append("Entry point Python con formato modulo:funcion.")
            if not self.state.python_version.strip():
                errors.append("La versión de Python es obligatoria.")
            gui = self.state.gui_entry_point.strip()
            if gui and ":" not in gui:
                errors.append("Entry GUI Python con formato modulo:funcion.")
        return self._store(errors)

    def validate_metadata(self) -> list[str]:
        errors = []
        name = self.state.name.strip()
        if not name:
            errors.append("El nombre es obligatorio.")
        elif not _NAME_PATTERN.match(name):
            errors.append("Nombre inválido (alfanumérico, ., _, -; debe empezar con alfanumérico).")
        elif name.lower() in _RESERVED_NAMES:
            errors.append(f"'{name}' es un nombre reservado del sistema AppImage.")
        if not _VERSION_PATTERN.match(self.state.version.strip()):
            errors.append("Versión inválida (semántica, ej: 1.0.0).")
        icon = self.state.icon.strip()
        if icon and not Path(icon).expanduser().exists():
            errors.append(f"Icono no encontrado: {icon}.")
        return self._store(errors)

    def validate_advanced(self) -> list[str]:
        errors = []
        update = self.state.update_information.strip()
        if update and not update.startswith(("gh-releases-", "zsync|")):
            errors.append("update_information debe empezar con 'gh-releases-' o 'zsync|'.")
        if self.state.sign and not self.state.sign_key.strip():
            errors.append("Firma activada sin Key ID (se usará la clave GPG por defecto).")
        for label, raw in (
            ("linuxdeploy", self.state.linuxdeploy_path),
            ("appimagetool", self.state.appimagetool_path),
        ):
            if raw.strip() and not Path(raw).expanduser().exists():
                errors.append(f"Binario local de {label} no existe: {raw}.")
        return self._store(errors)

    def validate_all(self) -> list[str]:
        errors: list[str] = []
        for validator in (
            self.validate_project,
            self.validate_type,
            self.validate_specific,
            self.validate_metadata,
        ):
            # validate_* ya llama a _store; acumular sin re-emitir de más.
            errors.extend([e for e in validator() if e not in errors])
        errors.extend(self.validate_advanced())
        return self._store(errors)

    def _store(self, errors: list[str]) -> list[str]:
        self._last_errors = errors
        self.validation_changed.emit(errors)
        return errors

    @property
    def last_errors(self) -> list[str]:
        return list(self._last_errors)

    # --- construcción de config del core ---

    def to_config(self) -> AppImageBuilderConfig:
        errors = self.validate_all()
        # La firma sin Key ID es solo aviso: no bloquea (gpg usa la por defecto).
        blocking = [e for e in errors if "sin Key ID" not in e]
        if blocking:
            raise ValueError("Configuración inválida: " + "; ".join(blocking))
        return self.state.to_config()
