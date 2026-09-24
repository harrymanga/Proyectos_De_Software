"""Pruebas de módulos GUI sin display (i18n, temas, config, workers)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from lang.i18n import Language
from themes.theme import THEMES, apply_theme
import config
from core.workers import _install_cmd, verify_magnets


def test_idiomas():
    lang = Language()
    assert lang.available() == ["en", "es"]
    assert lang.tr("btn.search") in ("Buscar", "Search")
    assert lang.set("en") is True
    assert lang.tr("btn.search") == "Search"
    assert lang.set("xx") is False
    assert lang.tr("no.existe") == "no.existe"
    es_keys = set(__import__("lang.i18n", fromlist=["STRINGS"]).STRINGS["es"])
    en_keys = set(__import__("lang.i18n", fromlist=["STRINGS"]).STRINGS["en"])
    assert es_keys == en_keys


def test_temas_paridad_y_aplicacion():
    assert set(THEMES["light"]) == set(THEMES["dark"])

    class W:
        def __init__(self):
            self.kw = {}

        def configure(self, **kw):
            self.kw.update(kw)

    raiz, log, list, state = W(), W(), W(), W()
    apply_theme(raiz, True, {"log": log, "list": list, "status": state})
    assert log.kw["bg"] == "#3a3a3a"
    apply_theme(raiz, False, {"log": log, "list": list, "status": state})
    assert log.kw["bg"] == "#ffffff"


def test_config_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.json")
    assert config.load_config(ruta) == {}
    config.save_config({"lang": "en"}, ruta)
    assert config.load_config(ruta) == {"lang": "en"}


def test_mensaje_libtorrent_menciona_gestor():
    texto = _install_cmd()
    assert any(g in texto for g in ("pacman", "apt", "dnf", "pip"))


def test_verify_sin_libtorrent_emite_error_y_done():
    eventos = []
    verify_magnets([], eventos.append)
    kinds = [k for k, _ in eventos]
    assert "error_libtorrent" in kinds and "done_verify" in kinds
