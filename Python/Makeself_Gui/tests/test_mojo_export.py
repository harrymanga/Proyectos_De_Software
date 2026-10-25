"""Backend MojoSetup: config.lua, vendor y export real (si hay binarios)."""
import os
import shutil
import subprocess
import sys
import zipfile

import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.mojo_export import (
    MojoExportError,
    MojoSettings,
    VENDOR_DIR,
    build_config_lua,
    detect_launcher,
    export_mojosetup,
    slugify,
    vendor_files,
    vendor_status,
)

HAS_VENDOR = os.path.isfile(os.path.join(VENDOR_DIR, "mojosetup"))
needs_vendor = pytest.mark.skipif(not HAS_VENDOR, reason="requiere scripts/build_mojosetup.sh")


def _stage(tmp_path, launcher=True):
    src = tmp_path / "src"
    (src / "game" / "sub").mkdir(parents=True)
    (src / "game" / "Spaced Name.bin").write_text("juego")
    (src / "game" / "sub" / "x.dat").write_text("anidado")
    if launcher:
        script = src / "start.sh"
        script.write_text("#!/bin/sh\necho ok\n")
        script.chmod(0o755)
    return src


def test_slugify():
    assert slugify("Hollow Knight Silksong 1.0") == "hollow-knight-silksong-1-0"
    assert slugify("***") == "miapp"


def test_detect_launcher(tmp_path):
    src = _stage(tmp_path, launcher=True)
    assert detect_launcher(str(src)) == "start.sh"


def test_detect_launcher_ignora_sh(tmp_path):
    src = _stage(tmp_path, launcher=False)
    assert detect_launcher(str(src)) == ""


def test_config_lua_obligatorios():
    cfg = build_config_lua(
        MojoSettings(launcher="start.sh", desktop_name="J", genericname="Juego"),
        5000, with_eula=True)
    # MojoSetup aborta si falta cualquiera de estos campos.
    assert "genericname =" in cfg
    assert "tooltip =" in cfg
    assert "icon =" in cfg
    assert 'commandline = "%0/start.sh"' in cfg
    assert "Setup.Eula" in cfg
    assert "TOTAL_INSTALL_SIZE = 5000" in cfg


def test_config_lua_escapa_comillas():
    cfg = build_config_lua(MojoSettings(description='Juego "X"'), 1, with_eula=False)
    assert '\\"X\\"' in cfg


def test_config_lua_sin_launcher_no_emite_menu():
    cfg = build_config_lua(MojoSettings(), 1, with_eula=False)
    assert "DesktopMenuItem" not in cfg


def test_vendor_status_reporta():
    ready, message = vendor_status()
    assert isinstance(ready, bool) and message
    files = vendor_files()
    assert set(files) == {"mojosetup", "make_self_extracting", "scripts"}


def test_export_exige_vendor(tmp_path):
    src = _stage(tmp_path)
    with pytest.raises(MojoExportError):
        export_mojosetup(str(src), str(tmp_path / "out.bin"), MojoSettings(),
                         vendor_dir=str(tmp_path / "no-existe"))


def test_export_rechaza_destino_dentro_de_origen(tmp_path):
    src = _stage(tmp_path)
    with pytest.raises(MojoExportError):
        export_mojosetup(str(src), str(src / "out.bin"), MojoSettings(),
                         vendor_dir=VENDOR_DIR)


@needs_vendor
def test_export_genera_instalador_valido(tmp_path):
    src = _stage(tmp_path)
    out = tmp_path / "instalador.bin"
    settings = MojoSettings(vendor="test.local", package_id="proto",
                            description="Proto", version="1.0",
                            destination=str(tmp_path / "dest"),
                            recommended=[], launcher=detect_launcher(str(src)))
    final = export_mojosetup(str(src), str(out), settings)
    assert final == str(out)
    assert out.is_file() and os.access(out, os.X_OK)
    # El ZIP anexado debe traer data/ y scripts/ con rutas relativas.
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "scripts/config.lua" in names
    assert any(n.startswith("data/game/") for n in names)
    assert "data/start.sh" not in names  # el lanzador no se duplica
    # Los plugins GUI van en la raíz, nunca dentro de data/ (evita
    # instalarlos en la carpeta del usuario).
    assert not any(n.startswith("data/guis/") for n in names)
    for name in names:
        assert not name.startswith("/") and ".." not in name


@needs_vendor
def test_export_instalacion_real(tmp_path):
    src = _stage(tmp_path)
    dest = tmp_path / "instalado"
    out = tmp_path / "inst.bin"
    export_mojosetup(str(src), str(out), MojoSettings(
        vendor="test.local", package_id="proto", description="Proto", version="1.0",
        destination=str(dest), recommended=[], launcher=detect_launcher(str(src)),
        desktop_name="Proto", genericname="Juego"))
    # MojoSetup necesita tty para su GUI stdio; script(1) lo simula.
    # MOJOSETUP_UI=stdio evita que un plugin GTK embebido intente abrir una
    # ventana durante los tests.
    env = dict(os.environ, MOJOSETUP_UI="stdio")
    result = subprocess.run(["script", "-qec", str(out), "/dev/null"],
                            capture_output=True, text=True, timeout=300,
                            stdin=subprocess.DEVNULL, env=env)
    combined = result.stdout + result.stderr
    assert "Installation was successful" in combined, combined[-800:]
    assert (dest / "game" / "Spaced Name.bin").is_file()
    assert (dest / "game" / "sub" / "x.dat").is_file()
    assert (dest / "uninstall-proto.sh").is_file()

def test_plugin_warning_detecta_gtk(tmp_path):
    from core.mojo_export import plugin_warning
    guis = tmp_path / "guis" / "x86_64"
    guis.mkdir(parents=True)
    (guis / "libmojosetupgui_gtkplus3.so").write_bytes(b"\x7fELF")
    aviso = plugin_warning(str(tmp_path))
    assert "Gtk3" in aviso and "PANIC" in aviso


def test_plugin_warning_sin_plugins(tmp_path):
    from core.mojo_export import plugin_warning
    assert plugin_warning(str(tmp_path)) == ""


def test_plugin_warning_vendor_actual_limpio():
    """El vendor del repo no debe llevar Gtk3 (provoca PANIC)."""
    from core.mojo_export import plugin_warning
    assert plugin_warning() == ""
