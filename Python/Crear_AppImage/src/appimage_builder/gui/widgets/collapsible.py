"""Sección colapsable sencilla (cabecera toggle + contenido)."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class CollapsibleSection(QWidget):
    """Contenedor con cabecera clicable que muestra/oculta el contenido."""

    def __init__(self, title: str, collapsed: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toggle = QPushButton()
        self.toggle.setCheckable(True)
        self.toggle.setChecked(not collapsed)
        self.toggle.setStyleSheet("text-align: left; font-weight: bold;")
        self.toggle.toggled.connect(self._on_toggled)
        layout.addWidget(self.toggle)

        self.content = QWidget()
        layout.addWidget(self.content)

        self._title = title
        self._sync(collapsed)

    def content_layout(self, layout) -> None:  # type: ignore[no-untyped-def]
        """Instala el layout del contenido (ej: QFormLayout)."""
        self.content.setLayout(layout)

    def is_collapsed(self) -> bool:
        return not self.toggle.isChecked()

    def set_collapsed(self, collapsed: bool) -> None:
        self.toggle.setChecked(not collapsed)

    def _on_toggled(self, checked: bool) -> None:
        self.content.setVisible(checked)
        self._update_arrow(checked)

    def _sync(self, collapsed: bool) -> None:
        self.content.setVisible(not collapsed)
        self._update_arrow(not collapsed)

    def _update_arrow(self, expanded: bool) -> None:
        arrow = "▾" if expanded else "▸"
        self.toggle.setText(f"{arrow} {self._title}")
