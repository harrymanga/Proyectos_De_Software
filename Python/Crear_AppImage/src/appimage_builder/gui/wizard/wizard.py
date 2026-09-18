"""Ensamblado del QWizard de 7 pasos."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWizard

from appimage_builder.gui.controllers.wizard_controller import WizardController
from appimage_builder.gui.settings import apply_defaults_to_state, load_settings
from appimage_builder.gui.state import WizardState
from appimage_builder.gui.viewmodels.wizard_viewmodel import WizardViewModel
from appimage_builder.gui.wizard.pages import (
    AdvancedPage,
    BuildPage,
    FinishPage,
    MetadataPage,
    SpecificPage,
    TypePage,
    WelcomePage,
)


class AppImageWizard(QWizard):
    """Wizard principal. ViewModel + controlador compartidos por las páginas."""

    def __init__(self, initial_path: Path | None = None) -> None:
        super().__init__()
        self.state = WizardState()
        if initial_path is not None:
            self.state.project_path = initial_path
        apply_defaults_to_state(self.state, load_settings())
        self.viewmodel = WizardViewModel(self.state)
        self.controller = WizardController(self.viewmodel)

        self.setWindowTitle("appimage-builder — Crear AppImage")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setMinimumSize(720, 520)

        # Botones en español (QWizard los trae en inglés por defecto).
        self.setButtonText(QWizard.WizardButton.BackButton, "Atrás")
        self.setButtonText(QWizard.WizardButton.NextButton, "Siguiente")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancelar")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finalizar")

        self.setPage(0, WelcomePage())
        self.setPage(1, TypePage())
        self.setPage(2, SpecificPage())
        self.setPage(3, MetadataPage())
        self.setPage(4, AdvancedPage())
        self.setPage(5, BuildPage())
        self.setPage(6, FinishPage())

        self.setStartId(0)

        build_page = self.page(5)
        assert isinstance(build_page, BuildPage)
        build_page.bind_controller(self.controller)

    def accept(self) -> None:  # type: ignore[override]
        """En la página final no cierra: vuelve a la bienvenida.

        Permite encadenar builds sin relanzar la app. Fuera de la página
        final mantiene el comportamiento estándar de QDialog.
        """
        page = self.currentPage()
        if page is not None and page.isFinalPage():
            self.restart()
            return
        super().accept()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Cancela un build en curso antes de cerrar (evita crash del hilo)."""
        if self.controller.is_build_running():
            self.controller.cancel_build()
            self.controller.wait_build(15000)
        super().closeEvent(event)
