"""El worker de Create propaga TMPDIR al proceso makeself."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.model import MakeselfProject
from gui.workers import CreateWorker


def _proyecto(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "setup.sh").write_text("#!/bin/sh\n")
    return MakeselfProject(str(src), str(tmp_path / "a.run"), "A", "./setup.sh")


def test_worker_propaga_tmpdir(tmp_path, monkeypatch):
    import gui.workers as workers_mod
    captured = {}

    def fake_stream(argv, on_progress, on_phase=None, file_total=0, env=None):
        captured["argv"] = argv
        captured["env"] = env
        return 0, "ok"

    monkeypatch.setattr(workers_mod, "stream_command", fake_stream)
    CreateWorker(_proyecto(tmp_path), "makeself", tmpdir=str(tmp_path)).run()
    assert captured["env"]["TMPDIR"] == str(tmp_path)


def test_worker_no_añade_flags_inexistentes(tmp_path, monkeypatch):
    import gui.workers as workers_mod
    captured = {}

    def fake_stream(argv, on_progress, on_phase=None, file_total=0, env=None):
        captured["argv"] = argv
        return 0, "ok"

    monkeypatch.setattr(workers_mod, "stream_command", fake_stream)
    CreateWorker(_proyecto(tmp_path), "makeself").run()
    # --nodiskspace pertenece al stub del .run, no al creador.
    assert "--nodiskspace" not in captured["argv"]
