"""Tests del wizard (offscreen, diálogos stubbed)."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from appimage_builder.core.constants import BuildType
from appimage_builder.gui.dialogs.settings_dialog import SettingsDialog
from appimage_builder.gui.settings import load_settings
from appimage_builder.gui.state import WizardState
from appimage_builder.gui.styles.themes import apply_theme
from appimage_builder.gui.viewmodels.wizard_viewmodel import WizardViewModel
from appimage_builder.gui.wizard.wizard import AppImageWizard


@pytest.fixture(autouse=True)
def _no_modal_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok),
    )


@pytest.mark.gui
def test_wizard_has_seven_pages(qapp, sample_python_project: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp
    wizard = AppImageWizard(initial_path=sample_python_project)
    assert len(wizard.pageIds()) == 7
    assert wizard.viewmodel.state is wizard.state
    assert wizard.controller.viewmodel is wizard.viewmodel


@pytest.mark.gui
def test_wizard_full_navigation(qapp, sample_python_project: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp
    wizard = AppImageWizard(initial_path=sample_python_project)
    wizard.restart()
    for page_id in range(7):
        page = wizard.page(page_id)
        page.initializePage()
        assert page.validatePage() is True, wizard.viewmodel.last_errors
    assert wizard.viewmodel.state.build_type == BuildType.PYTHON


@pytest.mark.gui
def test_metadata_live_validation(qapp, sample_python_project: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp
    wizard = AppImageWizard(initial_path=sample_python_project)
    page = wizard.page(3)
    page.initializePage()
    page.name_edit.setText("mal nombre!")
    assert page.live_error.text() != ""
    page.name_edit.setText("buen-nombre")
    assert page.live_error.text() == ""


@pytest.mark.gui
def test_wizard_buttons_in_spanish(qapp, sample_python_project: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp
    from PySide6.QtWidgets import QWizard

    wizard = AppImageWizard(initial_path=sample_python_project)
    texts = {
        QWizard.WizardButton.BackButton: "Atrás",
        QWizard.WizardButton.NextButton: "Siguiente",
        QWizard.WizardButton.CancelButton: "Cancelar",
        QWizard.WizardButton.FinishButton: "Finalizar",
    }
    for button, expected in texts.items():
        widget = wizard.button(button)
        assert widget is not None
        assert widget.text() == expected, button


@pytest.mark.gui
def test_finish_returns_to_welcome(qapp, sample_python_project: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp
    wizard = AppImageWizard(initial_path=sample_python_project)
    wizard.show()
    try:
        for _ in range(6):
            wizard.next()
        assert wizard.currentId() == 6
        wizard.accept()  # pulsar "Finalizar"
        assert wizard.isVisible()
        assert wizard.currentId() == 0
    finally:
        wizard.close()


@pytest.mark.gui
def test_viewmodel_blocks_invalid(qapp) -> None:  # type: ignore[no-untyped-def]
    del qapp
    viewmodel = WizardViewModel(WizardState())
    viewmodel.set_metadata(
        name="bad name!",
        version="x",
        description="",
        author="",
        license="MIT",
        homepage="",
        icon="",
    )
    assert len(viewmodel.validate_metadata()) == 2


@pytest.mark.gui
def test_settings_dialog_persists(qapp, isolated_home: Path) -> None:  # type: ignore[no-untyped-def]
    del qapp, isolated_home
    from PySide6.QtWidgets import QDialog

    dialog = SettingsDialog()
    dialog.cache_edit.setText("/tmp/aib-test-cache")
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert load_settings().cache_dir == "/tmp/aib-test-cache"


@pytest.mark.gui
def test_apply_theme_roundtrip(qapp) -> None:  # type: ignore[no-untyped-def]
    assert apply_theme(qapp, "oscuro") == "oscuro"
    assert qapp.styleSheet().strip() != ""
    assert apply_theme(qapp, "sistema") == "sistema"
    assert qapp.styleSheet() == ""
