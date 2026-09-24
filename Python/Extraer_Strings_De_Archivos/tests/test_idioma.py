"""Pruebas de idioma (sin Qt) y tema (con app simulada)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from i18n import Idioma, STRINGS
from themes.tema import DARK_QSS, LIGHT_QSS, apply_theme


def test_idiomas_disponibles():
    lang = Idioma()
    assert "es" in lang.available()
    assert "en" in lang.available()


def test_defecto_espanol():
    lang = Idioma()
    assert lang.current == "es"
    assert lang.tr("btn.extract") == "Extraer"


def test_cambio_ingles():
    lang = Idioma()
    assert lang.set("en") is True
    assert lang.tr("btn.extract") == "Extract"


def test_invalido_rechazado():
    lang = Idioma()
    assert lang.set("xx") is False
    assert lang.current == "es"


def test_clave_inexistente_devuelve_clave():
    lang = Idioma()
    assert lang.tr("no.existe") == "no.existe"


def test_parametros():
    lang = Idioma()
    assert lang.tr("status.files", n=2, dest="/tmp") == "2 archivo(s) | Destino: /tmp"
    lang.set("en")
    assert lang.tr("status.files", n=2, dest="/tmp") == "2 file(s) | Destination: /tmp"


def test_catalogos_mismas_claves():
    assert set(STRINGS["es"]) == set(STRINGS["en"])


def test_idioma_nuevo_sin_codigo():
    import json
    import tempfile
    import i18n as modulo
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "lang_xx.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"lang.name": "Xx", "btn.extract": "X"}, f)
        anterior = dict(modulo.STRINGS)
        modulo.STRINGS["xx"] = json.load(open(ruta, encoding="utf-8"))
        try:
            lang = Idioma()
            assert "xx" in lang.available()
            assert lang.name("xx") == "Xx"
        finally:
            modulo.STRINGS.clear()
            modulo.STRINGS.update(anterior)


class FakeApp:
    def __init__(self):
        self.stylesheet = None

    def setStyleSheet(self, value):
        self.stylesheet = value


def test_tema_oscuro_y_claro():
    app = FakeApp()
    apply_theme(app, True)
    assert app.stylesheet == DARK_QSS
    apply_theme(app, False)
    assert app.stylesheet == LIGHT_QSS
    assert DARK_QSS != LIGHT_QSS
