"""Preflight de espacio en disco."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.space import check_space, dir_size, fmt_size


def test_dir_size(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"x" * 100)
    assert dir_size(str(tmp_path)) == 100


def test_espacio_suficiente_no_avisa(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"x")
    assert check_space(str(tmp_path), str(tmp_path / "x.run"), str(tmp_path)) == []


def test_espacio_insuficiente_avisa(tmp_path, monkeypatch):
    import shutil
    (tmp_path / "a.bin").write_bytes(b"x" * 1000)

    class Usage:
        free = 10

    monkeypatch.setattr(shutil, "disk_usage", lambda _p: Usage())
    warnings = check_space(str(tmp_path), str(tmp_path / "x.run"), str(tmp_path))
    assert len(warnings) == 2
    assert fmt_size(1024).startswith("1.0 KB")


def test_uncompressed_kb():
    from core.space import uncompressed_kb
    assert uncompressed_kb("About to compress 7956092 KB of data...") == 7956092
    assert uncompressed_kb("sin datos") is None
