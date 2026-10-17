"""Tests bootstrap: builder + validator + inspector parse."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.builder import build_argv
from core.inspector import parse_info
from core.model import MakeselfProject
from core.validator import validate


def test_build_argv_basico():
    p = MakeselfProject("/tmp/app", "/tmp/app.run", "Etiqueta", "./setup.sh")
    argv = build_argv(p, "makeself")
    assert argv[:2] == ["makeself", "--gzip"]
    assert argv[-4:] == ["/tmp/app", "/tmp/app.run", "Etiqueta", "./setup.sh"]


def test_build_current_implica_notemp():
    p = MakeselfProject("/tmp/a", "/tmp/a.run", "L")
    p.options.current = True
    assert "--current" in build_argv(p)


def test_validate_dir_inexistente(tmp_path):
    p = MakeselfProject(str(tmp_path / "nodir"), "/tmp/x.run", "L", "")
    p.options.notemp = True
    errs = validate(p)
    assert any("archive_dir" in e for e in errs)


def test_parse_info_estilo_gog():
    txt = "Identification: Hollow Knight: Silksong (GOG.com)\nTarget directory: binaries\nCompression: gzip\nBuilt with Makeself version 2.2.0\nScript run after extraction:\n     ./startmojo.sh\n"
    info = parse_info(txt)
    assert info["identification"].startswith("Hollow Knight")
    assert info["script"] == "./startmojo.sh"
