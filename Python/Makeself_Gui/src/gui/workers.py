"""Workers en hilo para no bloquear la GUI (§58: hilos para I/O).

Cada worker emite progress(int): 0-100 con % real de makeself, -1 = ocupado
indeterminado. Al terminar emite finished_ok/failed.
"""
from __future__ import annotations

import os
import subprocess

from PySide6.QtCore import QThread, Signal

from core import append as append_mod
from core import inspector as inspector_mod
from core import runner as runner_mod
from core.builder import build_argv
from core.model import MakeselfProject
from core.progress import clean_output, count_files, count_tar_entries, detect_phase, find_percent
from core.validator import validate


def stream_command(argv: list[str], on_progress, on_phase=None,
                     file_total: int = 0, env=None) -> tuple[int, str]:
    """Ejecuta argv con stream y reporta % aunque venga sin saltos de línea.

    Makeself reescribe el progreso con backspaces en la misma línea, por eso
    se lee por bloques (no por líneas) y se devuelve el texto ya limpio.
    """
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=env)
    chunks: list[str] = []
    assert proc.stdout is not None
    carry = ""
    current_phase: str | None = None
    files_done = 0
    while True:
        block = proc.stdout.read(128)
        if not block:
            break
        chunks.append(block)
        window = carry + block
        pct = find_percent(window)
        if pct is not None:
            on_progress(pct)
        elif file_total > 0:
            files_done += count_tar_entries(window)
            on_progress(min(99, files_done * 100 // file_total))
        if on_phase is not None:
            phase = detect_phase(window)
            if phase is not None and phase != current_phase:
                current_phase = phase
                on_phase(phase)
        carry = window[-16:]
    proc.wait(timeout=1200)
    return proc.returncode, clean_output("".join(chunks))[-8000:]


class CreateWorker(QThread):
    finished_ok = Signal(int, str, str)
    failed = Signal(str)
    progress = Signal(int)
    phase = Signal(str)

    def __init__(self, project: MakeselfProject, makeself_bin: str, tmpdir: str = "") -> None:
        super().__init__()
        self.project = project
        self.makeself_bin = makeself_bin
        self.tmpdir = tmpdir

    def run(self) -> None:
        try:
            errors = validate(self.project)
            if errors:
                raise ValueError("; ".join(errors))
            self.progress.emit(-1)
            total = count_files(self.project.archive_dir)
            env = None
            if self.tmpdir:
                env = dict(os.environ, TMPDIR=self.tmpdir)
            code, out = stream_command(build_argv(self.project, self.makeself_bin),
                                       self.progress.emit, self.phase.emit,
                                       file_total=total, env=env)
            self.progress.emit(100)
            self.finished_ok.emit(code, out, "")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class InfoWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)
    progress = Signal(int)
    phase = Signal(str)

    def __init__(self, run_path: str) -> None:
        super().__init__()
        self.run_path = run_path

    def run(self) -> None:
        try:
            self.progress.emit(-1)
            self.finished_ok.emit(inspector_mod.run_info(self.run_path))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class ExtractWorker(QThread):
    finished_ok = Signal(int, str, str)
    failed = Signal(str)
    progress = Signal(int)
    phase = Signal(str)

    def __init__(self, run_path: str, dest: str) -> None:
        super().__init__()
        self.run_path = run_path
        self.dest = dest

    def run(self) -> None:
        try:
            self.progress.emit(-1)
            code, out = stream_command(
                ["sh", self.run_path, "--target", self.dest, "--noexec", "--keep"],
                self.progress.emit, self.phase.emit)
            self.finished_ok.emit(code, out, "")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class CheckWorker(QThread):
    finished_ok = Signal(int, str, str)
    failed = Signal(str)
    progress = Signal(int)
    phase = Signal(str)

    def __init__(self, run_path: str) -> None:
        super().__init__()
        self.run_path = run_path

    def run(self) -> None:
        try:
            self.progress.emit(-1)
            code, out = stream_command(["sh", self.run_path, "--check"], self.progress.emit, self.phase.emit)
            self.finished_ok.emit(code, out, "")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class AppendWorker(QThread):
    finished_ok = Signal(int, str, str)
    failed = Signal(str)
    progress = Signal(int)
    phase = Signal(str)

    def __init__(self, extra_dir: str, run_path: str, makeself_bin: str) -> None:
        super().__init__()
        self.extra_dir = extra_dir
        self.run_path = run_path
        self.makeself_bin = makeself_bin

    def run(self) -> None:
        try:
            if not os.path.isdir(self.extra_dir):
                raise ValueError(f"extra_dir no existe: {self.extra_dir}")
            self.progress.emit(-1)
            code, out = stream_command(
                [self.makeself_bin, "--append", self.extra_dir, self.run_path],
                self.progress.emit, self.phase.emit)
            self.finished_ok.emit(code, out, "")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
