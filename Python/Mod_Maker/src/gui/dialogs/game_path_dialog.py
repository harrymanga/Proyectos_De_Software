"""Diálogo genérico para configurar la ubicación de la carpeta de mods de un juego.

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import get_logger

logger = get_logger(__name__)


class GamePathDialog(QWidget):
    """Diálogo para configurar manualmente la carpeta de mods de cualquier juego."""

    def __init__(
        self,
        game_name: str,
        current_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.game_name = game_name
        self._selected_path: str | None = None
        self._setup_ui(current_path)

    def _setup_ui(self, current_path: str | None) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        label = QLabel(
            f"No se pudo detectar automáticamente la carpeta de mods de "
            f"{self.game_name}.\nSeleccione manualmente la carpeta donde están "
            f"instalados los mods."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        form = QHBoxLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(5)
        self.path_edit = QLineEdit()
        if current_path:
            self.path_edit.setText(current_path)
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self._browse)
        form.addWidget(self.path_edit)
        form.addWidget(browse_btn)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)

        self.accept_btn = QPushButton("Aceptar")
        self.accept_btn.clicked.connect(self._accept)
        btn_layout.addWidget(self.accept_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(lambda: self.setVisible(False))
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, f"Seleccionar carpeta de mods de {self.game_name}"
        )
        if folder:
            self.path_edit.setText(folder)

    def _accept(self) -> None:
        path_text = self.path_edit.text().strip()
        if not path_text:
            QMessageBox.warning(
                self,
                f"Configurar carpeta de mods — {self.game_name}",
                "Debe seleccionar una carpeta válida.",
            )
            return
        path = Path(path_text)
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(
                self,
                f"Configurar carpeta de mods — {self.game_name}",
                "La ruta seleccionada no es una carpeta válida.",
            )
            return
        self._selected_path = str(path)
        self._emit_selected()

    def _emit_selected(self) -> None:
        """Emite la señal de selección de ruta (para uso con contenedor padre)."""
        if hasattr(self.parent(), "on_game_path_selected"):
            self.parent().on_game_path_selected(self._selected_path)

    def get_selected_path(self) -> str | None:
        """Devuelve la ruta seleccionada por el usuario."""
        return self._selected_path
