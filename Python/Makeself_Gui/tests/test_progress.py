"""Parser de porcentaje de progreso."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.progress import find_percent


def test_encuentra_porcentaje():
    assert find_percent("Uncompressing App 0%  45%  100%") == 100
    assert find_percent("About to compress 4 KB") is None
    assert find_percent("") is None


def test_limita_rango():
    assert find_percent("999%") == 100


def test_clean_output_quita_backspaces():
    from core.progress import clean_output
    raw = "Verifying 63% \x08\x08\x08\x08\x08 64% done. All good."
    cleaned = clean_output(raw)
    assert "\x08" not in cleaned
    assert "64%" in cleaned
    assert "All good." in cleaned


def test_clean_output_comportamiento_terminal():
    from core.progress import clean_output
    assert clean_output("abc\x08\x08XY") == "aXY"


def test_detect_phase():
    from core.progress import detect_phase
    assert detect_phase("Verifying archive integrity...") == "verify"
    assert detect_phase("CRC checksums are OK") == "crc"
    assert detect_phase("SHA256 checksums are OK") == "sha256"
    assert detect_phase("MD5 checksums are OK") == "md5"
    assert detect_phase("Uncompressing App 10%") == "extract"
    assert detect_phase("About to compress 4 KB") == "compress"
    assert detect_phase("Hello world") is None


def test_count_tar_entries():
    from core.progress import count_tar_entries
    assert count_tar_entries("a ./data.bin\na ./setup.sh\n") == 2
    assert count_tar_entries("./data.bin\n./setup.sh\n") == 2
    assert count_tar_entries("About to compress 4 KB\n") == 0
    assert count_tar_entries("") == 0


def test_count_files(tmp_path):
    from core.progress import count_files
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("y")
    assert count_files(str(tmp_path)) == 2
