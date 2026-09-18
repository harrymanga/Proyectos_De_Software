"""Ajustes persistentes de la GUI (QSettings)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from appimage_builder.core.constants import (
    Architecture,
    Compression,
    coerce_architecture,
    coerce_compression,
)
from appimage_builder.gui.state import WizardState
from appimage_builder.gui.styles.themes import saved_theme

_ORG = "appimage-builder"
_APP = "appimage-builder"


@dataclass
class AppSettings:
    theme: str = "sistema"
    cache_dir: str = ""
    architecture: Architecture = Architecture.X86_64
    compression: Compression = Compression.XZ


def load_settings() -> AppSettings:
    """Lee los ajustes (con defaults sensatos si no existen)."""
    store = QSettings(_ORG, _APP)
    arch = store.value("defaults/architecture", Architecture.X86_64.value)
    comp = store.value("defaults/compression", Compression.XZ.value)
    return AppSettings(
        theme=saved_theme(),
        cache_dir=str(store.value("defaults/cache_dir", "") or ""),
        architecture=coerce_architecture(arch),
        compression=coerce_compression(comp),
    )


def save_settings(settings: AppSettings) -> None:
    """Persiste los ajustes."""
    from appimage_builder.gui.styles.themes import apply_theme

    store = QSettings(_ORG, _APP)
    store.setValue("defaults/cache_dir", settings.cache_dir)
    store.setValue("defaults/architecture", settings.architecture.value)
    store.setValue("defaults/compression", settings.compression.value)
    apply_theme(None, settings.theme)


def apply_defaults_to_state(state: WizardState, settings: AppSettings) -> None:
    """Aplica los defaults guardados a un estado fresco (no pisa entry/metadata)."""
    state.architecture = settings.architecture
    state.compression = settings.compression
    if settings.cache_dir.strip():
        state.cache_dir = settings.cache_dir.strip()
