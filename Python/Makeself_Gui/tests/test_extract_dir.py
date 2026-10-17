"""Carpeta de extracción a partir del nombre del .sh/.run."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.inspector import suggest_extract_dir


def test_sugiere_nombre_del_archivo(tmp_path):
    run = tmp_path / "mi-juego.sh"
    run.write_text("x")
    assert suggest_extract_dir(str(run)) == str(tmp_path / "mi-juego-extracted")


def test_evita_colisiones(tmp_path):
    run = tmp_path / "app.run"
    run.write_text("x")
    (tmp_path / "app-extracted").mkdir()
    assert suggest_extract_dir(str(run)) == str(tmp_path / "app-extracted-2")
