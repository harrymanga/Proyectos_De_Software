"""Widget de icono con drag&drop, preview y selector de archivo."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

_VALID_SUFFIXES = {".png", ".svg"}


class IconDropWidget(QWidget):
    """Muestra preview del icono; acepta arrastrar PNG/SVG o examinar."""

    icon_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QLabel("Sin icono")
        self.preview.setFixedSize(64, 64)
        self.preview.setFrameShape(QLabel.Shape.Box)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setAcceptDrops(True)
        self.preview.setToolTip("Arrastra un PNG/SVG aquí o usa Examinar…")
        layout.addWidget(self.preview)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("icon.png (opcional)")
        self.path_edit.setToolTip("Icono PNG/SVG. También puedes arrastrarlo al recuadro.")
        self.path_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.path_edit, 1)

        browse = QPushButton("Examinar…")
        browse.setToolTip("Buscar un archivo PNG o SVG en disco.")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)

        self.setAcceptDrops(True)

    # --- API ---

    def icon_path(self) -> str:
        return self._path

    def set_icon(self, path: str) -> None:
        self._path = path.strip()
        if self.path_edit.text() != self._path:
            self.path_edit.blockSignals(True)
            try:
                self.path_edit.setText(self._path)
            finally:
                self.path_edit.blockSignals(False)
        self._refresh_preview()
        self.icon_changed.emit(self._path)

    # --- internos ---

    def _on_text_changed(self, text: str) -> None:
        self._path = text.strip()
        self._refresh_preview()
        self.icon_changed.emit(self._path)

    def _browse(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar icono", self._path or str(Path.home()), "Imágenes (*.png *.svg)"
        )
        if chosen:
            self.set_icon(chosen)

    def _refresh_preview(self) -> None:
        if self._path and Path(self._path).expanduser().exists():
            pixmap = QPixmap(str(Path(self._path).expanduser()))
            if not pixmap.isNull():
                self.preview.setPixmap(
                    pixmap.scaled(
                        60,
                        60,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.preview.setPixmap(QPixmap())
        self.preview.setText("Sin icono")

    # --- drag & drop ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._urls_with_image(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if self._urls_with_image(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = self._urls_with_image(event)
        if urls:
            self.set_icon(urls[0])
            event.acceptProposedAction()
        else:
            event.ignore()

    @staticmethod
    def _urls_with_image(event: QDragEnterEvent | QDropEvent) -> list[str]:
        mime = event.mimeData()
        if mime is None or not mime.hasUrls():
            return []
        found = []
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            if Path(url.toLocalFile()).suffix.lower() in _VALID_SUFFIXES:
                found.append(url.toLocalFile())
        return found
