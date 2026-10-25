"""Parser de progreso de MojoSetup: porcentaje total y archivo en curso."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.progress import find_current_file, find_total_percent


def test_total_percent_basico():
    line = "f12.bin: 43% (total progress: 8%)\r"
    assert find_total_percent(line) == 8


def test_total_percent_toma_el_global():
    # El porcentaje por archivo (43%) no debe ganar al total (8%).
    assert find_total_percent("game/x.dat: 90% (total progress: 5%)") == 5


def test_total_percent_ignora_otras_lineas():
    assert find_total_percent("Installation was successful.") is None
    assert find_total_percent("") is None


def test_total_percent_limita_rango():
    assert find_total_percent("x: 1% (total progress: 150%)") == 100


def test_current_file():
    assert find_current_file("f12.bin: 43% (total progress: 8%)\r") == "f12.bin"
    assert find_current_file("game/sub/archivo largo.dat: 10% (total progress: 2%)") == \
        "game/sub/archivo largo.dat"
    assert find_current_file("sin porcentaje aqui") is None


def test_orden_de_prioridad_fase():
    """La fase install no debe pisar a done."""
    line = "a.dat: 100% (total progress: 100%)\rInstallation was successful.\r"
    assert find_total_percent(line) == 100