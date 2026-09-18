"""Worker que ejecuta el pipeline `BuildService` en un QThread.

El `asyncio.run()` vive dentro del hilo; la cancelación usa `threading.Event`
(compatible por duck-typing: el core solo llama a `.is_set()`), por lo que
`request_cancel()` es seguro desde el hilo GUI.

Nota de afinidad: el worker no tiene padre QObject (el controlador lo retiene
por referencia Python) para poder mudarse al hilo con `moveToThread`.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from appimage_builder.core.exceptions import CancellationError
from appimage_builder.core.models import AppImageBuilderConfig, BuildProgress
from appimage_builder.core.services.build_service import BuildService


class BuildWorker(QObject):
    """Orquesta `BuildService` en segundo plano con señales thread-safe."""

    progressed = Signal(float, str, str)  # fracción 0..1, mensaje, detalles
    stage_changed = Signal(str)  # nombre de la etapa actual
    log_line = Signal(str)  # línea de log para la vista
    finished_ok = Signal(str)  # ruta del AppImage como str
    failed = Signal(str)  # mensaje de error
    canceled = Signal()

    def __init__(
        self,
        config: AppImageBuilderConfig,
        project_root: Path,
    ) -> None:
        super().__init__()  # Sin padre: moveToThread lo exige.
        self.config = config
        self.project_root = project_root
        self.output_path: Path | None = None
        self._thread = QThread()
        self._cancel_event = threading.Event()
        self._cancel_requested = False
        self._ever_finished = False
        self.moveToThread(self._thread)
        self._thread.started.connect(self._execute)

    @property
    def thread(self) -> QThread:
        """Hilo interno (para conectar `finished` en el controlador)."""
        return self._thread

    # --- API pública (hilo GUI) ---

    def start(self) -> None:
        """Lanza el hilo (sin efecto si ya corre).

        Una cancelación pedida antes del primer arranque se respeta; tras una
        ejecución terminada, los flags se reinician para un reintento limpio.
        """
        if self._thread.isRunning():
            return
        if self._ever_finished:
            self._cancel_requested = False
            self._cancel_event.clear()
            self._ever_finished = False
        self.output_path = None
        self._thread.start()

    def request_cancel(self) -> None:
        """Pide cancelación cooperativa (thread-safe)."""
        self._cancel_requested = True
        self._cancel_event.set()

    def is_running(self) -> bool:
        return self._thread.isRunning()

    def wait(self, timeout_ms: int = 30000) -> bool:
        """Bloquea hasta que el hilo termina (para tests/cierre)."""
        return self._thread.wait(timeout_ms)

    # --- ejecución (hilo worker) ---

    def _execute(self) -> None:
        if self._cancel_requested:
            self._cancel_event.set()
        service = BuildService(
            project=self.config.project,
            build=self.config.build,
            project_root=self.project_root,
            runtime=self.config.runtime,
        )
        try:
            output = asyncio.run(self._run_service(service))
            if self._cancel_event.is_set():
                self.canceled.emit()
            else:
                self.output_path = output
                self.finished_ok.emit(str(output))
        except CancellationError:
            self.canceled.emit()
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            try:
                service.cleanup()
            except Exception:
                pass
            self._ever_finished = True
            self._thread.quit()

    async def _run_service(self, service: BuildService) -> Path:
        last_stage = ""

        async def forward(update: BuildProgress) -> None:
            nonlocal last_stage
            if update.stage != last_stage:
                last_stage = update.stage
                self.stage_changed.emit(update.stage)
            self.progressed.emit(update.progress, update.message, update.details)
            if update.details:
                self.log_line.emit(f"[{update.stage}] {update.details}")
            elif update.message:
                self.log_line.emit(f"[{update.stage}] {update.message}")

        return await service.build(
            progress_callback=forward,
            cancel_event=self._cancel_event,  # type: ignore[arg-type]
        )
