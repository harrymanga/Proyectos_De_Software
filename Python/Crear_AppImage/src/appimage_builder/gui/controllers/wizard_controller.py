"""Controlador del wizard: detección, config y ciclo de vida del worker."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from appimage_builder.core.models import AppImageBuilderConfig
from appimage_builder.gui.viewmodels.wizard_viewmodel import WizardViewModel
from appimage_builder.gui.workers.build_worker import BuildWorker


class WizardController(QObject):
    """Coordina viewmodel ↔ worker. La Fase 6 conectará estas señales a BuildPage."""

    # Re-emisiones del worker para que la vista solo conozca al controlador.
    build_progressed = Signal(float, str, str)
    build_stage_changed = Signal(str)
    build_log_line = Signal(str)
    build_finished = Signal(str)
    build_failed = Signal(str)
    build_canceled = Signal()

    def __init__(self, viewmodel: WizardViewModel, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._worker: BuildWorker | None = None

    # --- detección y config ---

    def detect_project(self, path: Path | str) -> None:
        self.viewmodel.set_project_path(path)
        self.viewmodel.detect()

    def build_config(self) -> AppImageBuilderConfig:
        """Config validada lista para el core (lanza ValueError si es inválida)."""
        return self.viewmodel.to_config()

    # --- ciclo de vida del worker ---

    def is_build_running(self) -> bool:
        return self._worker is not None and self._worker.is_running()

    def start_build(self) -> BuildWorker:
        """Valida, crea el worker y lo lanza. Lanza ValueError/RuntimeError."""
        self._cleanup_worker()
        if self.is_build_running():
            raise RuntimeError("Ya hay un build en curso.")
        config = self.build_config()  # valida primero (no crear hilos inútiles)
        worker = BuildWorker(config, self.viewmodel.state.project_path.expanduser())
        worker.progressed.connect(self.build_progressed.emit)
        worker.stage_changed.connect(self.build_stage_changed.emit)
        worker.log_line.connect(self.build_log_line.emit)
        worker.finished_ok.connect(self.build_finished.emit)
        worker.failed.connect(self.build_failed.emit)
        worker.canceled.connect(self.build_canceled.emit)
        self._worker = worker
        worker.start()
        return worker

    def cancel_build(self) -> None:
        if self._worker is not None:
            self._worker.request_cancel()

    def wait_build(self, timeout_ms: int = 60000) -> bool:
        """Espera al worker y libera la referencia (determinista sin event loop)."""
        worker = self._worker
        if worker is None:
            return True
        finished = worker.wait(timeout_ms)
        if finished:
            self._cleanup_worker()
        return finished

    def _cleanup_worker(self) -> None:
        worker = self._worker
        if worker is not None and not worker.is_running():
            self._worker = None
