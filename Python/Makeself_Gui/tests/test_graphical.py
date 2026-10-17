"""Plantilla graphical: modo consola y modo GUI (stub de zenity)."""
import os
import shutil
import subprocess
import sys

import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.templates import generate_scaffold

ZENITY_STUB = """#!/bin/sh
for a in "$@"; do
  case "$a" in
    --file-selection*) echo "$STUB_DEST"; exit 0;;
    --progress*) cat > "$STUB_PROGRESS_LOG"; exit 0;;
  esac
done
exit 0
"""


def _stage(tmp_path, label="Mi Juego 1.0"):
    stage = tmp_path / "stage"
    created = generate_scaffold("graphical", str(stage), label)
    assert "setup.sh" in created
    (stage / "game.dat").write_text("datos")
    exe = stage / "game.bin"
    exe.write_text("#!/bin/sh\necho launched\n")
    exe.chmod(0o755)
    return stage


def test_graphical_sintaxis(tmp_path):
    stage = _stage(tmp_path)
    result = subprocess.run(["sh", "-n", str(stage / "setup.sh")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_graphical_modo_consola(tmp_path):
    stage = _stage(tmp_path)
    dest = tmp_path / "dest"
    env = dict(os.environ, DISPLAY="")
    result = subprocess.run(["sh", str(stage / "setup.sh"), str(dest)],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
    assert (dest / "game.dat").is_file()
    assert (dest / "uninstall.sh").is_file()
    assert not (dest / "setup.sh").exists()


def test_graphical_modo_gui_con_stub(tmp_path, monkeypatch):
    stage = _stage(tmp_path)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "zenity").write_text(ZENITY_STUB)
    (bindir / "zenity").chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    dest = tmp_path / "gui-dest"
    progress_log = tmp_path / "progress.log"
    env = dict(os.environ,
               DISPLAY=":0",
               HOME=str(home),
               STUB_DEST=str(dest),
               STUB_PROGRESS_LOG=str(progress_log),
               PATH=str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    result = subprocess.run(["sh", str(stage / "setup.sh")],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
    assert (dest / "game.dat").is_file()
    assert (dest / "uninstall.sh").is_file()
    assert "100" in progress_log.read_text()
    slug = "mi-juego-1-0"
    assert (home / ".local" / "bin" / slug).is_symlink()
    assert (home / ".local" / "share" / "applications" / f"{slug}.desktop").is_file()


DF_STUB = """#!/bin/sh
for a in "$@"; do
  case "$a" in
    *lleno*) echo "fs 100 95 5 95% /x"; exit 0;;
  esac
done
echo "fs 1000000 100 999900 1% /x"
"""


def _env_with_stubs(tmp_path, extra_stubs=()):
    bindir = tmp_path / "sbin"
    bindir.mkdir(exist_ok=True)
    (bindir / "df").write_text(DF_STUB)
    (bindir / "df").chmod(0o755)
    for name, content in extra_stubs:
        (bindir / name).write_text(content)
        (bindir / name).chmod(0o755)
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=str(home),
               PATH=str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    return env, bindir


def test_consola_aborta_sin_espacio(tmp_path):
    stage = _stage(tmp_path)
    env, _bindir = _env_with_stubs(tmp_path)
    dest = tmp_path / "disco-lleno"
    result = subprocess.run(["sh", str(stage / "setup.sh"), "--nogui", str(dest)],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 1
    assert "Sin espacio" in result.stderr
    assert not (dest / "game.dat").exists()


def test_gui_repide_destino_sin_espacio(tmp_path):
    stateful_stub = """#!/bin/sh
for a in "$@"; do
  case "$a" in
    --file-selection*)
      n=$(cat "$STUB_COUNT_FILE" 2>/dev/null || echo 0)
      n=$((n+1)); echo "$n" > "$STUB_COUNT_FILE"
      if [ "$n" -eq 1 ]; then echo "$STUB_DEST_1"; else echo "$STUB_DEST_2"; fi
      exit 0;;
    --progress*) cat > "$STUB_PROGRESS_LOG"; exit 0;;
  esac
done
exit 0
"""
    stage = _stage(tmp_path)
    env, _bindir = _env_with_stubs(tmp_path, [("zenity", stateful_stub)])
    lleno = tmp_path / "disco-lleno"
    amplio = tmp_path / "disco-amplio"
    env.update({"DISPLAY": ":0",
                "STUB_DEST_1": str(lleno), "STUB_DEST_2": str(amplio),
                "STUB_COUNT_FILE": str(tmp_path / "count.txt"),
                "STUB_PROGRESS_LOG": str(tmp_path / "p.log")})
    result = subprocess.run(["sh", str(stage / "setup.sh"), str(lleno)],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
    assert (amplio / "game.dat").is_file()
    assert not (lleno / "game.dat").exists()


MAKESELF_BIN = shutil.which("makeself")
needs_makeself = pytest.mark.skipif(MAKESELF_BIN is None, reason="requiere makeself")

LOG_STUB = """#!/bin/sh
echo "$@" >> "$STUB_CALLS_LOG"
for a in "$@"; do
  case "$a" in
    --file-selection*) echo "$STUB_DEST"; exit 0;;
    --progress*) cat > "$STUB_PROGRESS_LOG"; exit 0;;
  esac
done
exit 0
"""


def _gui_env(tmp_path, dest):
    bindir = tmp_path / "gbin"
    bindir.mkdir(exist_ok=True)
    (bindir / "zenity").write_text(LOG_STUB)
    (bindir / "zenity").chmod(0o755)
    home = tmp_path / "ghome"
    home.mkdir(exist_ok=True)
    env = dict(os.environ,
               DISPLAY=":0",
               HOME=str(home),
               STUB_DEST=str(dest),
               STUB_CALLS_LOG=str(tmp_path / "calls.log"),
               STUB_PROGRESS_LOG=str(tmp_path / "gp.log"),
               PATH=str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    return env


def _build_run(stage, run_path):
    result = subprocess.run(
        [MAKESELF_BIN, "--nox11", str(stage), str(run_path), "Juego Verif", "./setup.sh"],
        capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr


@needs_makeself
def test_gui_muestra_verificacion_del_paquete(tmp_path):
    stage = _stage(tmp_path)
    run_path = tmp_path / "juego.run"
    _build_run(stage, run_path)
    dest = tmp_path / "vdest"
    env = _gui_env(tmp_path, dest)
    result = subprocess.run(["sh", str(run_path)],
                            capture_output=True, text=True, timeout=120, env=env)
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls.log").read_text()
    assert "Verificando integridad" in calls
    assert "MD5" in calls
    assert "checksums are OK" in calls
    assert (dest / "game.dat").is_file()


@needs_makeself
def test_gui_skip_verify_omite_verificacion(tmp_path):
    stage = _stage(tmp_path)
    run_path = tmp_path / "juego2.run"
    _build_run(stage, run_path)
    dest = tmp_path / "vdest2"
    env = _gui_env(tmp_path, dest)
    result = subprocess.run(["sh", str(run_path), "--", "--skip-verify"],
                            capture_output=True, text=True, timeout=120, env=env)
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls.log").read_text()
    assert "Verificando integridad" not in calls
    assert (dest / "game.dat").is_file()


def test_setup_directo_no_se_autoverifica(tmp_path):
    stage = _stage(tmp_path)
    dest = tmp_path / "vdest3"
    env = _gui_env(tmp_path, dest)
    result = subprocess.run(["sh", str(stage / "setup.sh"), str(dest)],
                            capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls.log").read_text()
    assert "Verificando integridad" not in calls
    assert (dest / "game.dat").is_file()
