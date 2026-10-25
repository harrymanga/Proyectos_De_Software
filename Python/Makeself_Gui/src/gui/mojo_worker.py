"""Worker en hilo para exportar un instalador MojoSetup."""
from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from core import mojo_export


class MojoExportWorker(QThread):
    finished_ok = Signal(str, str)  # ruta_final, detalle
    failed = Signal(str)

    def __init__(self, archive_dir: str, output: str, settings) -> None:
        super().__init__()
        self.archive_dir = archive_dir
        self.output = output
        self.settings = settings

    def run(self) -> None:
        try:
            final = mojo_export.export_mojosetup(
                self.archive_dir, self.output, self.settings)
            self.finished_ok.emit(final, str(self.settings))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{exc}\n{traceback.format_exc(limit=3)}")