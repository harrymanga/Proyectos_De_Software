"""Las 7 páginas del wizard (widgets + sincronización con el viewmodel).

La BuildPage ejecuta el pipeline real vía `WizardController` (Fase 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from appimage_builder.core.constants import Architecture, BuildType, Compression
from appimage_builder.gui.styles.themes import apply_theme, available_themes, saved_theme
from appimage_builder.gui.widgets.collapsible import CollapsibleSection
from appimage_builder.gui.widgets.icon_drop import IconDropWidget

if TYPE_CHECKING:
    from appimage_builder.gui.wizard.wizard import AppImageWizard


def _wizard(page: QWizardPage) -> AppImageWizard:
    wiz = page.wizard()
    assert wiz is not None
    return wiz  # type: ignore[return-value]


class WelcomePage(QWizardPage):
    """Paso 1: bienvenida + selección del proyecto con auto-detección."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Bienvenido a appimage-builder")
        self.setSubTitle("Selecciona el proyecto a empaquetar como AppImage.")

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Crea AppImages de tus aplicaciones Python, nativas o binarios sueltos.")
        )

        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("/ruta/a/tu/proyecto")
        self.path_edit.setToolTip("Directorio raíz del proyecto a empaquetar.")
        browse = QPushButton("Examinar…")
        browse.setToolTip("Elegir el directorio del proyecto.")
        browse.clicked.connect(self._browse)
        row.addWidget(self.path_edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)

        self.detected_label = QLabel("")
        self.detected_label.setWordWrap(True)
        layout.addWidget(self.detected_label)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(available_themes())
        self.theme_combo.setToolTip("Tema de la interfaz (se guarda entre sesiones).")
        self.theme_combo.currentTextChanged.connect(self._change_theme)
        theme_row.addWidget(self.theme_combo)
        settings_button = QPushButton("Ajustes…")
        settings_button.setToolTip("Cache y valores por defecto (persisten).")
        settings_button.clicked.connect(self._open_settings)
        theme_row.addWidget(settings_button)
        theme_row.addStretch(1)
        layout.addLayout(theme_row)
        layout.addStretch(1)

    def _change_theme(self, name: str) -> None:
        apply_theme(None, name)

    def _open_settings(self) -> None:
        from appimage_builder.gui.dialogs.settings_dialog import SettingsDialog
        from appimage_builder.gui.settings import apply_defaults_to_state, load_settings

        dialog = SettingsDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            apply_defaults_to_state(_wizard(self).viewmodel.state, load_settings())

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Seleccionar proyecto", self.path_edit.text() or str(Path.home())
        )
        if chosen:
            self.path_edit.setText(chosen)
            self._refresh_detection()

    def _refresh_detection(self) -> None:
        wiz = _wizard(self)
        wiz.controller.detect_project(self.path_edit.text().strip() or ".")
        detected = wiz.viewmodel.state.detected_type
        if detected is not None:
            self.detected_label.setText(
                f"Detectado: <b>{detected.value}</b>"
                + (
                    f" — entry point sugerido: <code>{wiz.viewmodel.state.detected_entry}</code>"
                    if wiz.viewmodel.state.detected_entry
                    else ""
                )
            )
        else:
            self.detected_label.setText("")

    def initializePage(self) -> None:
        self.path_edit.setText(str(_wizard(self).viewmodel.state.project_path))
        self.theme_combo.blockSignals(True)
        try:
            self.theme_combo.setCurrentText(saved_theme())
        finally:
            self.theme_combo.blockSignals(False)
        self._refresh_detection()

    def validatePage(self) -> bool:
        wiz = _wizard(self)
        wiz.controller.detect_project(self.path_edit.text().strip() or ".")
        errors = wiz.viewmodel.validate_project()
        if errors:
            QMessageBox.warning(self, "Ruta inválida", errors[0])
            return False
        return True


class TypePage(QWizardPage):
    """Paso 2: confirmar o corregir el tipo de proyecto detectado."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Tipo de proyecto")
        self.setSubTitle("Confirma la detección automática o corrígela.")

        layout = QVBoxLayout(self)
        self.group = QButtonGroup(self)
        self.buttons: dict[BuildType, QRadioButton] = {}
        for build_type in (BuildType.PYTHON, BuildType.NATIVE, BuildType.GENERIC):
            radio = QRadioButton(f"{build_type.display_name} — {build_type.description}")
            radio.setToolTip(build_type.description)
            self.group.addButton(radio)
            self.buttons[build_type] = radio
            layout.addWidget(radio)

        form = QFormLayout()
        self.entry_edit = QLineEdit()
        self.entry_edit.setPlaceholderText("main:main (Python) o nombre del binario")
        self.entry_edit.setToolTip("Python: modulo:funcion. Nativo/genérico: nombre del binario.")
        form.addRow("Entry point:", self.entry_edit)
        layout.addLayout(form)
        layout.addStretch(1)

    def initializePage(self) -> None:
        state = _wizard(self).viewmodel.state
        self.buttons[state.build_type].setChecked(True)
        self.entry_edit.setText(state.entry_point)

    def validatePage(self) -> bool:
        vm = _wizard(self).viewmodel
        for build_type, radio in self.buttons.items():
            if radio.isChecked():
                vm.set_build_type(build_type)
        vm.set_entry_point(self.entry_edit.text())
        errors = vm.validate_type()
        if errors:
            QMessageBox.warning(self, "Tipo inválido", errors[0])
            return False
        return True


class SpecificPage(QWizardPage):
    """Paso 3: configuración específica del tipo (stack dinámico)."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Configuración específica")
        self.setSubTitle("Opciones según el tipo de proyecto elegido.")

        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Python ---
        python_tab = QWidget()
        python_form = QFormLayout(python_tab)
        self.py_entry = QLineEdit()
        self.py_entry.setPlaceholderText("modulo:funcion (ej: main:main)")
        self.py_entry.setToolTip("Función de entrada del paquete Python.")
        self.py_gui_entry = QLineEdit()
        self.py_gui_entry.setPlaceholderText("modulo:funcion GUI (opcional, ej: gui.main:main)")
        self.py_gui_entry.setToolTip("Si se define, el AppImage lanza la GUI con --gui.")
        self.py_version = QComboBox()
        self.py_version.addItems(["3.10", "3.11", "3.12", "3.13"])
        self.py_version.setToolTip("Versión del runtime Python empaquetado.")
        python_form.addRow("Entry point:", self.py_entry)
        python_form.addRow("Entry GUI:", self.py_gui_entry)
        python_form.addRow("Versión Python:", self.py_version)
        self.stack.addWidget(python_tab)

        # --- Nativo ---
        native_tab = QWidget()
        native_form = QFormLayout(native_tab)
        self.native_binary = QLineEdit()
        self.native_binary.setPlaceholderText("Nombre del binario resultante")
        self.native_binary.setToolTip("Nombre del ejecutable que generará la compilación.")
        self.native_system = QLabel("")
        native_form.addRow("Binario:", self.native_binary)
        native_form.addRow("Sistema detectado:", self.native_system)
        self.stack.addWidget(native_tab)

        # --- Genérico ---
        generic_tab = QWidget()
        generic_form = QFormLayout(generic_tab)
        row = QHBoxLayout()
        self.generic_exe = QLineEdit()
        self.generic_exe.setPlaceholderText("Ruta o nombre del ejecutable")
        self.generic_exe.setToolTip("Binario precompilado a empaquetar tal cual.")
        generic_browse = QPushButton("Examinar…")
        generic_browse.clicked.connect(self._browse_exe)
        row.addWidget(self.generic_exe, 1)
        row.addWidget(generic_browse)
        generic_form.addRow("Ejecutable:", row)
        self.stack.addWidget(generic_tab)

    def _browse_exe(self) -> None:
        wiz = _wizard(self)
        chosen, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar ejecutable", str(wiz.state.project_path)
        )
        if chosen:
            self.generic_exe.setText(chosen)

    def initializePage(self) -> None:
        state = _wizard(self).viewmodel.state
        index = {
            BuildType.PYTHON: 0,
            BuildType.NATIVE: 1,
            BuildType.GENERIC: 2,
        }[state.build_type]
        self.stack.setCurrentIndex(index)
        self.py_entry.setText(state.entry_point)
        self.py_gui_entry.setText(state.gui_entry_point)
        self.py_version.setCurrentText(state.python_version)
        self.native_binary.setText(state.entry_point)
        self.native_system.setText(self._detect_native_system(state.project_path))
        self.generic_exe.setText(state.entry_point)

    @staticmethod
    def _detect_native_system(root: Path) -> str:
        if (root / "Cargo.toml").exists():
            return "cargo"
        if (root / "go.mod").exists():
            return "go"
        if (root / "CMakeLists.txt").exists():
            return "cmake"
        if (root / "meson.build").exists():
            return "meson"
        if (root / "Makefile").exists() or (root / "makefile").exists():
            return "make"
        return "no detectado"

    def validatePage(self) -> bool:
        vm = _wizard(self).viewmodel
        if vm.state.build_type == BuildType.PYTHON:
            vm.set_entry_point(self.py_entry.text())
            vm.set_gui_entry_point(self.py_gui_entry.text())
            vm.set_python_version(self.py_version.currentText())
        elif vm.state.build_type == BuildType.NATIVE:
            vm.set_entry_point(self.native_binary.text())
        else:
            vm.set_entry_point(self.generic_exe.text())
        errors = vm.validate_specific()
        if errors:
            QMessageBox.warning(self, "Configuración inválida", errors[0])
            return False
        return True


class MetadataPage(QWizardPage):
    """Paso 4: metadatos de la aplicación + icono."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Metadatos")
        self.setSubTitle("Nombre, versión, descripción e icono (arrastrable).")

        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Alfanumérico, ., _ y -. No usar nombres reservados (usr, bin…).")
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1.0.0")
        self.version_edit.setToolTip("Versión semántica: MAJOR.MINOR.PATCH (ej: 1.0.0).")
        self.desc_edit = QLineEdit()
        self.desc_edit.setToolTip("Descripción corta que verán los usuarios.")
        self.author_edit = QLineEdit()
        self.license_combo = QComboBox()
        self.license_combo.setEditable(True)
        self.license_combo.addItems(["MIT", "Apache-2.0", "GPL-3.0-only", "BSD-3-Clause"])
        self.license_combo.setToolTip("Licencia del proyecto.")
        self.homepage_edit = QLineEdit()
        self.homepage_edit.setPlaceholderText("https://…")
        self.homepage_edit.setToolTip("Web del proyecto (opcional).")

        self.icon_widget = IconDropWidget()
        self.icon_widget.setToolTip("Icono PNG/SVG: arrástralo al recuadro o examina.")

        form.addRow("Nombre:", self.name_edit)
        form.addRow("Versión:", self.version_edit)
        form.addRow("Descripción:", self.desc_edit)
        form.addRow("Autor:", self.author_edit)
        form.addRow("Licencia:", self.license_combo)
        form.addRow("Web:", self.homepage_edit)
        form.addRow("Icono:", self.icon_widget)

        # Validación en vivo: hint rojo bajo el formulario.
        self.live_error = QLabel("")
        self.live_error.setStyleSheet("color: red;")
        self.live_error.setWordWrap(True)
        form.addRow(self.live_error)
        self._initializing = False
        self.name_edit.textChanged.connect(lambda _t: self._live_validate())
        self.version_edit.textChanged.connect(lambda _t: self._live_validate())
        self.icon_widget.icon_changed.connect(lambda _p: self._live_validate())

    def initializePage(self) -> None:
        state = _wizard(self).viewmodel.state
        self._initializing = True
        try:
            self.name_edit.setText(state.name)
            self.version_edit.setText(state.version)
            self.desc_edit.setText(state.description)
            self.author_edit.setText(state.author)
            self.license_combo.setCurrentText(state.license)
            self.homepage_edit.setText(state.homepage)
            self.icon_widget.set_icon(state.icon)
        finally:
            self._initializing = False
        self._live_validate()

    def _push_to_viewmodel(self) -> None:
        _wizard(self).viewmodel.set_metadata(
            name=self.name_edit.text(),
            version=self.version_edit.text(),
            description=self.desc_edit.text(),
            author=self.author_edit.text(),
            license=self.license_combo.currentText(),
            homepage=self.homepage_edit.text(),
            icon=self.icon_widget.icon_path(),
        )

    def _live_validate(self) -> None:
        """Actualiza el hint rojo sin diálogos (validación en vivo)."""
        if self._initializing:
            return
        vm = _wizard(self).viewmodel
        self._push_to_viewmodel()
        errors = vm.validate_metadata()
        self.live_error.setText(errors[0] if errors else "")

    def validatePage(self) -> bool:
        self._push_to_viewmodel()
        errors = _wizard(self).viewmodel.validate_metadata()
        if errors:
            QMessageBox.warning(self, "Metadatos inválidos", errors[0])
            return False
        return True


class AdvancedPage(QWizardPage):
    """Paso 5: opciones avanzadas con secciones colapsables."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Opciones avanzadas")
        self.setSubTitle("Arquitectura, compresión, firma y salida.")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.arch_combo = QComboBox()
        for arch in Architecture:
            self.arch_combo.addItem(arch.display_name, arch)
        self.arch_combo.setToolTip("Arquitectura del AppImage (debe coincidir con tu sistema).")
        self.comp_combo = QComboBox()
        for comp in Compression:
            self.comp_combo.addItem(f"{comp.value} — {comp.description}", comp)
        self.comp_combo.setToolTip("xz: mejor ratio. zstd: más rápido. gzip/lzo: compatibles.")

        out_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("<proyecto>/dist")
        self.output_edit.setToolTip("Carpeta donde se escribirá el .AppImage.")
        out_browse = QPushButton("Examinar…")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(out_browse)
        out_widget = QWidget()
        out_widget.setLayout(out_row)

        form.addRow("Arquitectura:", self.arch_combo)
        form.addRow("Compresión:", self.comp_combo)
        form.addRow("Salida:", out_widget)
        self.bundle_check = QCheckBox("Empaquetar árbol completo (genérico)")
        self.bundle_check.setToolTip(
            "Copia todo el proyecto al AppDir para apps portables con datos "
            "relativos. Solo aplica a tipo genérico."
        )
        form.addRow(self.bundle_check)
        layout.addLayout(form)

        self.sign_section = CollapsibleSection("Firma GPG", collapsed=True)
        sign_form = QFormLayout()
        self.sign_check = QCheckBox("Firmar con GPG")
        self.sign_check.setToolTip("Firma el AppImage para verificar su origen.")
        self.sign_key = QLineEdit()
        self.sign_key.setPlaceholderText("Key ID (opcional)")
        self.sign_key.setToolTip("ID de la clave (vacío = clave por defecto de GPG).")
        self.sign_key.setEnabled(False)
        self.sign_check.toggled.connect(self.sign_key.setEnabled)
        sign_form.addRow(self.sign_check)
        sign_form.addRow("Clave GPG:", self.sign_key)
        self.sign_section.content_layout(sign_form)
        layout.addWidget(self.sign_section)

        self.update_section = CollapsibleSection("Actualización y entorno", collapsed=True)
        update_form = QFormLayout()
        self.update_edit = QLineEdit()
        self.update_edit.setPlaceholderText("gh-releases-… o zsync|… (opcional)")
        self.update_edit.setToolTip("Información de actualización integrada (AppImageUpdate).")
        self.no_fuse_check = QCheckBox("Sin FUSE (APPIMAGE_EXTRACT_AND_RUN)")
        self.no_fuse_check.setToolTip("Para sistemas sin FUSE: extrae y ejecuta.")

        cache_row = QHBoxLayout()
        self.cache_edit = QLineEdit()
        self.cache_edit.setPlaceholderText("~/.cache/appimage-builder")
        self.cache_edit.setToolTip("Cache de linuxdeploy/appimagetool descargados.")
        cache_browse = QPushButton("Examinar…")
        cache_browse.clicked.connect(self._browse_cache)
        cache_row.addWidget(self.cache_edit, 1)
        cache_row.addWidget(cache_browse)
        cache_widget = QWidget()
        cache_widget.setLayout(cache_row)

        update_form.addRow("Update info:", self.update_edit)
        update_form.addRow(self.no_fuse_check)
        update_form.addRow("Cache:", cache_widget)

        linuxdeploy_row = QHBoxLayout()
        self.linuxdeploy_edit = QLineEdit()
        self.linuxdeploy_edit.setPlaceholderText("Binario local (vacío = descargar)")
        self.linuxdeploy_edit.setToolTip("Ruta a linuxdeploy-*.AppImage local (sin red).")
        linuxdeploy_browse = QPushButton("Examinar…")
        linuxdeploy_browse.clicked.connect(
            lambda: self._browse_tool(self.linuxdeploy_edit, "linuxdeploy")
        )
        linuxdeploy_row.addWidget(self.linuxdeploy_edit, 1)
        linuxdeploy_row.addWidget(linuxdeploy_browse)
        linuxdeploy_widget = QWidget()
        linuxdeploy_widget.setLayout(linuxdeploy_row)

        appimagetool_row = QHBoxLayout()
        self.appimagetool_edit = QLineEdit()
        self.appimagetool_edit.setPlaceholderText("Binario local (vacío = descargar)")
        self.appimagetool_edit.setToolTip("Ruta a appimagetool-*.AppImage local (sin red).")
        appimagetool_browse = QPushButton("Examinar…")
        appimagetool_browse.clicked.connect(
            lambda: self._browse_tool(self.appimagetool_edit, "appimagetool")
        )
        appimagetool_row.addWidget(self.appimagetool_edit, 1)
        appimagetool_row.addWidget(appimagetool_browse)
        appimagetool_widget = QWidget()
        appimagetool_widget.setLayout(appimagetool_row)

        update_form.addRow("linuxdeploy:", linuxdeploy_widget)
        update_form.addRow("appimagetool:", appimagetool_widget)
        self.update_section.content_layout(update_form)
        layout.addWidget(self.update_section)
        layout.addStretch(1)

    def _browse_tool(self, target: QLineEdit, name: str) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, f"Binario local de {name}", target.text() or str(Path.home())
        )
        if chosen:
            target.setText(chosen)

    def _browse_cache(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Directorio de cache")
        if chosen:
            self.cache_edit.setText(chosen)

    def _browse_output(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Directorio de salida")
        if chosen:
            self.output_edit.setText(chosen)

    def initializePage(self) -> None:
        state = _wizard(self).viewmodel.state
        self.arch_combo.setCurrentIndex(self.arch_combo.findData(state.architecture))
        self.comp_combo.setCurrentIndex(self.comp_combo.findData(state.compression))
        self.output_edit.setText(state.output)
        self.bundle_check.setChecked(state.bundle_tree)
        self.bundle_check.setEnabled(state.build_type == BuildType.GENERIC)
        self.sign_check.setChecked(state.sign)
        self.sign_key.setText(state.sign_key)
        self.update_edit.setText(state.update_information)
        self.no_fuse_check.setChecked(state.no_fuse)
        self.cache_edit.setText(state.cache_dir)
        self.linuxdeploy_edit.setText(state.linuxdeploy_path)
        self.appimagetool_edit.setText(state.appimagetool_path)

    def validatePage(self) -> bool:
        from appimage_builder.core.constants import coerce_architecture, coerce_compression

        vm = _wizard(self).viewmodel
        vm.set_advanced(
            architecture=coerce_architecture(self.arch_combo.currentData()),
            compression=coerce_compression(self.comp_combo.currentData()),
            output=self.output_edit.text(),
            sign=self.sign_check.isChecked(),
            sign_key=self.sign_key.text(),
            update_information=self.update_edit.text(),
            no_fuse=self.no_fuse_check.isChecked(),
            cache_dir=self.cache_edit.text(),
            bundle_tree=self.bundle_check.isChecked() and self.bundle_check.isEnabled(),
            linuxdeploy_path=self.linuxdeploy_edit.text(),
            appimagetool_path=self.appimagetool_edit.text(),
        )
        errors = [e for e in vm.validate_advanced() if "sin Key ID" not in e]
        if errors:
            QMessageBox.warning(self, "Opciones inválidas", errors[0])
            return False
        return True


class BuildPage(QWizardPage):
    """Paso 6: ejecuta el build en un worker con progreso en tiempo real."""

    STAGES = (
        "preparing",
        "downloading_runtime",
        "installing_deps",
        "running_linuxdeploy",
        "creating_appimage",
        "signing",
    )

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Build")
        self.setSubTitle("Ejecuta el build y sigue el progreso en tiempo real.")

        self._controller = None  # type: ignore[assignment]
        self._current_stage = ""
        self._last_result: str | None = None  # None | "ok" | "fail" | "cancel"
        self._artifact = ""

        layout = QVBoxLayout(self)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        stages_group = QGroupBox("Etapas")
        stages_layout = QFormLayout(stages_group)
        self.stage_bars: dict[str, QProgressBar] = {}
        for stage in self.STAGES:
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            stages_layout.addRow(self._stage_label(stage) + ":", bar)
            self.stage_bars[stage] = bar
        layout.addWidget(stages_group)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Los logs del build aparecerán aquí…")
        layout.addWidget(self.log_view, 1)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.run_button = QPushButton("Iniciar build")
        self.run_button.setToolTip("Ejecuta el pipeline completo en segundo plano.")
        self.run_button.clicked.connect(self._on_run)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setToolTip("Cancela el build en curso de forma cooperativa.")
        self.cancel_button.clicked.connect(self._on_cancel)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    @staticmethod
    def _stage_label(stage: str) -> str:
        from appimage_builder.core.constants import BuildStage

        for member in BuildStage:
            if member.value == stage:
                return member.display_name
        return stage

    # --- conexión con el controlador (una vez, desde el wizard) ---

    def bind_controller(self, controller) -> None:  # type: ignore[no-untyped-def]
        self._controller = controller
        controller.build_stage_changed.connect(self._on_stage_changed)
        controller.build_progressed.connect(self._on_progressed)
        controller.build_log_line.connect(self.append_log)
        controller.build_finished.connect(self._on_finished)
        controller.build_failed.connect(self._on_failed)
        controller.build_canceled.connect(self._on_canceled)

    # --- ciclo de página ---

    def initializePage(self) -> None:
        state = _wizard(self).viewmodel.state
        try:
            config = state.to_config()
            self.summary_label.setText(
                f"Listo para construir <b>{config.project.name}</b> "
                f"{config.project.version} ({config.project.build_type.value}) → "
                f"<code>{config.build.output}</code>"
            )
        except Exception as e:
            self.summary_label.setText(f"<b style='color:red'>Config inválida:</b> {e}")
        if self._controller is not None and self._controller.is_build_running():
            self._reflect_running()
        elif self._last_result is None:
            self._reset_bars()

    def validatePage(self) -> bool:
        if self._controller is not None and self._controller.is_build_running():
            QMessageBox.warning(
                self,
                "Build en curso",
                "Espera a que termine o cancela el build antes de continuar.",
            )
            return False
        return True

    # --- botones ---

    def _on_run(self) -> None:
        if self._controller is None:
            return
        try:
            self._controller.start_build()
        except ValueError as e:
            self.status_label.setText(f"<b style='color:red'>Config inválida:</b> {e}")
            return
        except RuntimeError as e:
            self.status_label.setText(f"<b style='color:red'>{e}</b>")
            return
        self._last_result = None
        self._artifact = ""
        self.log_view.clear()
        self._reset_bars()
        self._reflect_running()
        self.status_label.setText("<b>En curso…</b>")

    def _on_cancel(self) -> None:
        if self._controller is not None:
            self._controller.cancel_build()
            self.status_label.setText("Cancelando…")

    # --- slots del worker (vía controlador) ---

    def _on_stage_changed(self, stage: str) -> None:
        if stage == "completed":
            for bar in self.stage_bars.values():
                bar.setValue(100)
            self.progress.setValue(100)
            return
        if stage in self.stage_bars:
            self._current_stage = stage
            idx = self.STAGES.index(stage)
            for earlier in self.STAGES[:idx]:
                self.stage_bars[earlier].setValue(100)

    def _on_progressed(self, frac: float, message: str, _details: str) -> None:
        frac = max(0.0, min(1.0, frac))
        if self._current_stage in self.stage_bars:
            idx = self.STAGES.index(self._current_stage)
            self.stage_bars[self._current_stage].setValue(int(frac * 100))
            self.progress.setValue(int((idx + frac) / len(self.STAGES) * 100))
        if message:
            self.status_label.setText(message)

    def _on_finished(self, output: str) -> None:
        self._last_result = "ok"
        self._artifact = output
        for bar in self.stage_bars.values():
            bar.setValue(100)
        self.progress.setValue(100)
        self.status_label.setText(f"<b style='color:green'>Completado:</b> {output}")
        self._reflect_idle()

    def _on_failed(self, message: str) -> None:
        self._last_result = "fail"
        self.status_label.setText(f"<b style='color:red'>Falló:</b> {message}")
        self.append_log(f"ERROR: {message}")
        self._reflect_idle()

    def _on_canceled(self) -> None:
        self._last_result = "cancel"
        self.status_label.setText("<b>Cancelado por el usuario.</b>")
        self.append_log("Build cancelado.")
        self._reflect_idle()

    # --- helpers de UI ---

    def append_log(self, text: str) -> None:
        self.log_view.append(text)

    def set_progress(self, percent: float, message: str = "") -> None:
        self.progress.setValue(int(max(0.0, min(1.0, percent)) * 100))
        if message:
            self.append_log(message)

    def _reset_bars(self) -> None:
        for bar in self.stage_bars.values():
            bar.setValue(0)
        self.progress.setValue(0)
        self._current_stage = ""

    def _reflect_running(self) -> None:
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self._set_nav_enabled(False)

    def _reflect_idle(self) -> None:
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self._set_nav_enabled(True)

    def _set_nav_enabled(self, enabled: bool) -> None:
        wiz = self.wizard()
        if wiz is not None:
            back_btn = wiz.button(QWizard.WizardButton.BackButton)
            next_btn = wiz.button(QWizard.WizardButton.NextButton)
            if back_btn is not None:
                back_btn.setEnabled(enabled)
            if next_btn is not None:
                next_btn.setEnabled(enabled)


class FinishPage(QWizardPage):
    """Paso 7: finalización con acciones (abrir carpeta, copiar ruta)."""

    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Finalización")
        self.setSubTitle("Revisa el resultado y accede al AppImage.")
        self.setFinalPage(True)

        layout = QVBoxLayout(self)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        group = QGroupBox("Acciones")
        group_layout = QVBoxLayout(group)
        self.open_button = QPushButton("Abrir carpeta de salida")
        self.open_button.clicked.connect(self._open_output)
        self.copy_button = QPushButton("Copiar ruta del AppImage")
        self.copy_button.clicked.connect(self._copy_path)
        self.template_button = QPushButton("Guardar como plantilla")
        self.template_button.setToolTip(
            "Guarda la configuración actual como plantilla reutilizable."
        )
        self.template_button.clicked.connect(self._save_template)
        group_layout.addWidget(self.open_button)
        group_layout.addWidget(self.copy_button)
        group_layout.addWidget(self.template_button)
        layout.addWidget(group)
        layout.addStretch(1)

    def _expected_artifact(self) -> Path:
        state = _wizard(self).state
        config = state.to_config()
        return (
            config.build.output
            / f"{config.project.name}-{config.build.architecture.value}.AppImage"
        )

    def initializePage(self) -> None:
        try:
            artifact = self._expected_artifact()
            self.summary_label.setText(f"AppImage esperado en:<br><code>{artifact}</code>")
        except Exception as e:
            self.summary_label.setText(f"<b style='color:red'>Config inválida:</b> {e}")

    def _open_output(self) -> None:
        try:
            folder = self._expected_artifact().parent
            folder.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        except Exception as e:
            QMessageBox.warning(self, "No se pudo abrir", str(e))

    def _copy_path(self) -> None:
        try:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(str(self._expected_artifact()))
        except Exception as e:
            QMessageBox.warning(self, "No se pudo copiar", str(e))

    def _save_template(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        from appimage_builder.core.services.template_store import TemplateStore

        name, ok = QInputDialog.getText(self, "Guardar plantilla", "Nombre:")
        if not ok or not name.strip():
            return
        try:
            config = _wizard(self).viewmodel.to_config()
            dest = TemplateStore().save(name.strip(), config)
            QMessageBox.information(self, "Plantilla guardada", f"Guardada en:\n{dest}")
        except Exception as e:
            QMessageBox.warning(self, "No se pudo guardar", str(e))
