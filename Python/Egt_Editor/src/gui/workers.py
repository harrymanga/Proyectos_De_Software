"""I/O en hilos (§58: no bloquear GUI)."""
from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args) -> None:
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self) -> None:  # noqa: D102
        try:
            self.done.emit(self._fn(*self._args))
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))
