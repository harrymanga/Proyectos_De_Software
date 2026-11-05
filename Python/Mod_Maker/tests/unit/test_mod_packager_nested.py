"""Pruebas adicionales para mod_packager con estructura de carpetas anidadas."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.core.mod_packager import build_mod_zip


def test_build_mod_zip_with_nested_folder(tmp_path: Path) -> None:
    """build_mod_zip funciona con mods que tienen carpeta contenedora (ej. DiscoScience_2.0.1/)."""
    source = tmp_path / "source_mod"
    mod_folder = source / "DiscoScience_2.0.1"
    mod_folder.mkdir(parents=True)
    (mod_folder / "info.json").write_text(
        json.dumps({"name": "DiscoScience", "version": "2.0.1"}), encoding="utf-8"
    )
    (mod_folder / "data.lua").write_text("-- test\n", encoding="utf-8")

    output = tmp_path / "out.zip"
    result = build_mod_zip(mod_folder, output)

    assert result == output
    assert output.exists()
    assert zipfile.is_zipfile(output)

    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert "DiscoScience/info.json" in names
        assert "DiscoScience/data.lua" in names


def test_build_mod_zip_with_info_json_in_subfolder(tmp_path: Path) -> None:
    """build_mod_zip encuentra info.json en subcarpeta cuando source_dir es el padre."""
    source = tmp_path / "source_mod"
    mod_folder = source / "MiMod"
    mod_folder.mkdir(parents=True)
    (mod_folder / "info.json").write_text(
        json.dumps({"name": "MiMod", "version": "1.0.0"}), encoding="utf-8"
    )
    (mod_folder / "data.lua").write_text("-- test\n", encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = build_mod_zip(mod_folder, output_dir)

    expected = output_dir / "MiMod_1.0.0.zip"
    assert result == expected
    assert expected.exists()
