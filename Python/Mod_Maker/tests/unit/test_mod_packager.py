"""Pruebas unitarias para mod_packager (empaquetado unificado de mods)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.core.mod_packager import build_mod_zip


def test_build_mod_zip_creates_valid_zip(tmp_path: Path) -> None:
    """build_mod_zip crea un ZIP válido con info.json dentro de la carpeta del mod."""
    source = tmp_path / "source_mod"
    source.mkdir()
    (source / "info.json").write_text(
        json.dumps({"name": "TestMod", "version": "1.0.0"}), encoding="utf-8"
    )
    (source / "data.lua").write_text("-- test\n", encoding="utf-8")

    output = tmp_path / "TestMod_1.0.0.zip"
    result = build_mod_zip(source, output)

    assert result == output
    assert output.exists()
    assert zipfile.is_zipfile(output)

    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert "TestMod/info.json" in names
        assert "TestMod/data.lua" in names


def test_build_mod_zip_rejects_missing_info_json(tmp_path: Path) -> None:
    """build_mod_zip rechaza carpetas sin info.json."""
    source = tmp_path / "source_mod"
    source.mkdir()
    (source / "data.lua").write_text("-- test\n", encoding="utf-8")

    output = tmp_path / "out.zip"

    try:
        build_mod_zip(source, output)
        assert False, "Debería haber lanzado SecurityError"
    except Exception as exc:  # pragma: no cover - defensivo
        assert "info.json" in str(exc)


def test_build_mod_zip_rejects_invalid_metadata(tmp_path: Path) -> None:
    """build_mod_zip rechaza info.json sin campos requeridos."""
    source = tmp_path / "source_mod"
    source.mkdir()
    (source / "info.json").write_text(
        json.dumps({"version": "1.0.0"}), encoding="utf-8"  # falta "name"
    )

    output = tmp_path / "out.zip"

    try:
        build_mod_zip(source, output)
        assert False, "Debería haber lanzado SecurityError"
    except Exception as exc:  # pragma: no cover - defensivo
        assert "name" in str(exc) or "campo obligatorio" in str(exc)


def test_build_mod_zip_output_is_directory(tmp_path: Path) -> None:
    """build_mod_zip genera nombre automático si output es directorio."""
    source = tmp_path / "source_mod"
    source.mkdir()
    (source / "info.json").write_text(
        json.dumps({"name": "MiMod", "version": "2.0.0"}), encoding="utf-8"
    )

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = build_mod_zip(source, output_dir)

    expected = output_dir / "MiMod_2.0.0.zip"
    assert result == expected
    assert expected.exists()


def test_build_mod_zip_blocks_dangerous_extension(tmp_path: Path) -> None:
    """build_mod_zip bloquea archivos .exe peligrosos."""
    source = tmp_path / "source_mod"
    source.mkdir()
    (source / "info.json").write_text(
        json.dumps({"name": "TestMod", "version": "1.0.0"}), encoding="utf-8"
    )
    (source / "virus.exe").write_text("malicious", encoding="utf-8")
    (source / "data.lua").write_text("-- ok\n", encoding="utf-8")

    output = tmp_path / "out.zip"
    build_mod_zip(source, output)

    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert "TestMod/virus.exe" not in names
        assert "TestMod/data.lua" in names
        assert "TestMod/info.json" in names
