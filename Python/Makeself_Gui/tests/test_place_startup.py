"""place_startup: relativiza o copia el script inicial dentro de archive_dir."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.project import place_startup


def test_relativiza_si_esta_dentro(tmp_path):
    script = tmp_path / "setup.sh"
    script.write_text("echo hola")
    rel, copied = place_startup(str(tmp_path), str(script))
    assert rel == "./setup.sh"
    assert copied is False


def test_copia_si_esta_fuera(tmp_path):
    archive = tmp_path / "app"
    archive.mkdir()
    outside = tmp_path / "otro.sh"
    outside.write_text("echo x")
    rel, copied = place_startup(str(archive), str(outside))
    assert copied is True
    assert (archive / "otro.sh").is_file()
    assert rel == "./otro.sh"


def test_no_sobrescribe_distinto(tmp_path):
    archive = tmp_path / "app"
    archive.mkdir()
    (archive / "setup.sh").write_text("viejo")
    outside = tmp_path / "setup.sh"
    outside.write_text("nuevo")
    rel, copied = place_startup(str(archive), str(outside))
    assert copied is True
    assert (archive / "setup.sh").read_text() == "viejo"
    assert rel == "./setup-1.sh"
