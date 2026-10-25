"""Worker para ejecutar operaciones de I/O en segundo plano (no bloquean la GUI).

Norma §58: hilos para I/O para mantener la interfaz responsiva.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class WorkerSignals(QObject):
    """Señales del worker."""

    finished = Signal(object)
    error = Signal(str)
    result = Signal(object)
    progress = Signal(str)


class Worker(QRunnable):
    """Worker que ejecuta una función en el hilo global de Qt."""

    def __init__(self, fn, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:  # noqa: D401
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # pragma: no cover - defensivo
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit(result)


def run_in_background(fn, *args, on_result=None, on_error=None, on_finished=None, **kwargs):
    """Ejecuta una función en segundo plano usando el thread pool de Qt.

    Args:
        fn: Función a ejecutar.
        *args: Argumentos posicionales para fn.
        on_result: Callback llamado con el resultado cuando termina con éxito.
        on_error: Callback llamado con el mensaje de error si falla.
        on_finished: Callback llamado siempre al terminar.
        **kwargs: Argumentos nombrados para fn.

    Returns:
        El objeto Worker creado.
    """
    worker = Worker(fn, *args, **kwargs)

    if on_result is not None:
        worker.signals.result.connect(on_result)
    if on_error is not None:
        worker.signals.error.connect(on_error)
    if on_finished is not None:
        worker.signals.finished.connect(on_finished)

    QThreadPool.globalInstance().start(worker)
    return worker
