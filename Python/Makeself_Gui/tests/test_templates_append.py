"""Tests: plantillas generan esqueleto válido + append construye argv correcto."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.templates import TEMPLATES, generate_scaffold


def test_plantillas_generan_esqueleto(tmp_path):
    for tpl in TEMPLATES:
        dest = tmp_path / tpl
        created = generate_scaffold(tpl, str(dest), "Juego 1.0")
        assert created
        assert (dest / "data").is_dir()
        if tpl == "mojosetup":
            assert (dest / "startmojo.sh").is_file()
            assert (dest / "scripts" / "config.lua").is_file()
        else:
            assert (dest / "setup.sh").is_file()


def test_universal_instala_con_espacios(tmp_path):
    from core.templates import generate_scaffold
    import subprocess
    stage = tmp_path / "stage"
    generate_scaffold("universal", str(stage), "Hollow Knight Silksong")
    payload = stage / "data" / "Hollow Knight Silksong"
    payload.write_text("binario-falso")
    dest = tmp_path / "destino con espacios"
    result = subprocess.run(
        ["sh", str(stage / "setup.sh"), str(dest)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert (dest / "Hollow Knight Silksong").is_file()
    assert (dest / "uninstall.sh").is_file()
    assert "--list" in (stage / "setup.sh").read_text()


def test_universal_ignora_data_vacia(tmp_path):
    from core.templates import generate_scaffold
    import subprocess
    stage = tmp_path / "stage"
    generate_scaffold("universal", str(stage), "Juego Top")
    (stage / "game.dat").write_text("datos")
    dest = tmp_path / "dest"
    result = subprocess.run(
        ["sh", str(stage / "setup.sh"), str(dest)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert (dest / "game.dat").is_file()


def test_universal_aborta_sin_espacio(tmp_path):
    from core.templates import generate_scaffold
    import subprocess
    stage = tmp_path / "stage"
    generate_scaffold("universal", str(stage), "Juego Top")
    (stage / "game.dat").write_text("datos")
    bindir = tmp_path / "sbin"
    bindir.mkdir()
    (bindir / "df").write_text(
        '#!/bin/sh\necho "fs 100 95 5 95% /x"\n')
    (bindir / "df").chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home),
               PATH=str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    dest = tmp_path / "dest"
    result = subprocess.run(["sh", str(stage / "setup.sh"), str(dest)],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 1
    assert "Sin espacio" in result.stderr


def test_append_valida_entradas(tmp_path):
    from core.append import append_to_archive
    import pytest
    with pytest.raises(ValueError):
        append_to_archive(str(tmp_path / "nodir"), str(tmp_path / "no.run"))


def test_append_argv(monkeypatch, tmp_path):
    import subprocess
    from core import append as append_mod
    captured = {}

    class FakeResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    extra = tmp_path / "extra"
    extra.mkdir()
    run = tmp_path / "a.run"
    run.write_text("x")
    result = append_mod.append_to_archive(str(extra), str(run), "makeself")
    assert result.returncode == 0
    assert captured["argv"][:3] == ["makeself", "--append", str(extra)]
