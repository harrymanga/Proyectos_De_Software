"""Diálogo genérico para configurar la ubicación de la carpeta de mods de un juego."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.core.i18n import translate
from src.core.logger import get_logger

logger = get_logger(__name__)


class GamePathDialog(QDialog):
    """Diálogo para configurar manualmente la carpeta de mods de cualquier juego."""

    def __init__(
        self,
        game_name: str,
        current_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.game_name = game_name
        self.setWindowTitle(f"Configurar carpeta de mods — {game_name}")
        self.setMinimumWidth(500)
        self._selected_path: str | None = None
        self._setup_ui(current_path)

    def _setup_ui(self, current_path: str | None) -> None:
        layout = QVBoxLayout(self)

        label = QLabel(
            f"No se pudo detectar automáticamente la carpeta de mods de "
            f"{self.game_name}.\nSeleccione manualmente la carpeta donde están "
            f"instalados los mods."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        form = QHBoxLayout()
        self.path_edit = QLineEdit()
        if current_path:
            self.path_edit.setText(current_path)
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self._browse)
        form.addWidget(self.path_edit)
        form.addWidget(browse_btn)
        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        layout.addWidget(self.button_box)

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
        self.accept()

    def get_selected_path(self) -> str | None:
        """Devuelve la ruta seleccionada por el usuario."""
        return self._selected_path
