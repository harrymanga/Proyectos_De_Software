"""Diálogo de ajustes: tema, cache y defaults de arquitectura/compresión."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from appimage_builder.core.constants import Architecture, Compression
from appimage_builder.gui.settings import AppSettings, load_settings, save_settings
from appimage_builder.gui.styles.themes import available_themes


class SettingsDialog(QDialog):
    """Edita y persiste `AppSettings`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajustes")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(available_themes())
        self.theme_combo.setToolTip("Tema de la interfaz.")
        form.addRow("Tema:", self.theme_combo)

        cache_row = QHBoxLayout()
        self.cache_edit = QLineEdit()
        self.cache_edit.setPlaceholderText("~/.cache/appimage-builder (vacío = defecto)")
        self.cache_edit.setToolTip("Cache de herramientas descargadas.")
        cache_browse = QPushButton("Examinar…")
        cache_browse.clicked.connect(self._browse_cache)
        cache_row.addWidget(self.cache_edit, 1)
        cache_row.addWidget(cache_browse)
        cache_widget = QWidget()
        cache_widget.setLayout(cache_row)
        form.addRow("Cache:", cache_widget)

        self.arch_combo = QComboBox()
        for arch in Architecture:
            self.arch_combo.addItem(arch.display_name, arch)
        self.arch_combo.setToolTip("Arquitectura por defecto para proyectos nuevos.")
        form.addRow("Arquitectura:", self.arch_combo)

        self.comp_combo = QComboBox()
        for comp in Compression:
            self.comp_combo.addItem(f"{comp.value} — {comp.description}", comp)
        self.comp_combo.setToolTip("Compresión por defecto.")
        form.addRow("Compresión:", self.comp_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_current()

    def _browse_cache(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Directorio de cache")
        if chosen:
            self.cache_edit.setText(chosen)

    def _load_current(self) -> None:
        current = load_settings()
        self.theme_combo.setCurrentText(current.theme)
        self.cache_edit.setText(current.cache_dir)
        self.arch_combo.setCurrentIndex(self.arch_combo.findData(current.architecture))
        self.comp_combo.setCurrentIndex(self.comp_combo.findData(current.compression))

    def settings(self) -> AppSettings:
        from appimage_builder.core.constants import coerce_architecture, coerce_compression

        return AppSettings(
            theme=self.theme_combo.currentText(),
            cache_dir=self.cache_edit.text().strip(),
            architecture=coerce_architecture(self.arch_combo.currentData()),
            compression=coerce_compression(self.comp_combo.currentData()),
        )

    def accept(self) -> None:
        save_settings(self.settings())
        super().accept()
