"""Ejecuta un instalador MojoSetup con tty real para recibir su progreso.

MojoSetup comprueba `isatty()`: sin terminal no escribe nada. Por eso este worker
levanta un pseudo-terminal con `pty` y lee de ahí, en vez de depender de `script(1)`.
"""
from __future__ import annotations

import os
import pty
import select
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QThread, Signal

from core.progress import clean_output, find_current_file, find_total_percent

MOJO_PHASES = {
    "verify": "Verificando integridad",
    "extract": "Instalando archivos",
    "metadata": "Escribiendo manifiesto",
    "done": "Instalación completa",
}


class MojoInstallWorker(QThread):
    """Lanza el instalador MojoSetup y transmite progreso real (0-100)."""

    progress = Signal(int)          # porcentaje total
    phase = Signal(str)             # clave de fase
    current_file = Signal(str)      # archivo en curso
    finished_ok = Signal(int, str)  # rc, salida limpia
    failed = Signal(str)

    def __init__(self, installer: str, ui: str = "stdio", timeout: int = 7200) -> None:
        super().__init__()
        self.installer = installer
        self.ui = ui
        self.timeout = timeout

    def run(self) -> None:
        if not os.path.isfile(self.installer):
            self.failed.emit(f"no existe el instalador: {self.installer}")
            return
        env = dict(os.environ, MOJOSETUP_UI=self.ui, TERM="dumb")
        try:
            master, slave = pty.openpty()
        except OSError as exc:
            self.failed.emit(f"no se pudo crear un terminal: {exc}")
            return
        try:
            proc = subprocess.Popen(
                [self.installer],
                stdin=slave, stdout=slave, stderr=slave,
                env=env, close_fds=True,
            )
        except OSError as exc:
            os.close(master)
            os.close(slave)
            self.failed.emit(str(exc))
            return
        os.close(slave)

        chunks: list[str] = []
        carry = ""
        phase = None
        deadline_checks = 0
        while True:
            try:
                readable, _, _ = select.select([master], [], [], 1.0)
            except (OSError, ValueError):
                break
            if proc.poll() is not None and not readable:
                break
            if not readable:
                deadline_checks += 1
                if deadline_checks > self.timeout:
                    proc.kill()
                    self.failed.emit("tiempo de espera agotado durante la instalación")
                    return
                continue
            try:
                data = os.read(master, 4096)
            except OSError:
                break
            if not data:
                break
            text = data.decode("utf-8", "replace")
            chunks.append(text)
            window = carry + text
            pct = find_total_percent(window)
            if pct is not None:
                self.progress.emit(pct)
            name = find_current_file(window)
            if name:
                self.current_file.emit(name)
            lowered = window.lower()
            if "installation was successful" in lowered:
                if phase != "done":
                    phase = "done"
                    self.phase.emit("done")
                    self.progress.emit(100)
            elif pct is not None and phase is None:
                phase = "extract"
                self.phase.emit("extract")
            elif ".mojosetup" in lowered and phase == "extract":
                phase = "metadata"
                self.phase.emit("metadata")
            carry = window[-32:]
        os.close(master)
        proc.wait()

        output = clean_output("".join(chunks))
        if proc.returncode == 0 and "installation was successful" not in output.lower():
            # El instalador terminó bien pero no lo confirmó (p. ej. destino ya
            # instalado); no es un error.
            pass
        self.finished_ok.emit(proc.returncode, output)