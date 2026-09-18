"""Wizard de 7 pasos (esqueleto Fase 4; ejecución real en Fase 6)."""

from appimage_builder.gui.wizard.pages import (
    AdvancedPage,
    BuildPage,
    FinishPage,
    MetadataPage,
    SpecificPage,
    TypePage,
    WelcomePage,
)
from appimage_builder.gui.wizard.wizard import AppImageWizard

__all__ = [
    "AdvancedPage",
    "AppImageWizard",
    "BuildPage",
    "FinishPage",
    "MetadataPage",
    "SpecificPage",
    "TypePage",
    "WelcomePage",
]
