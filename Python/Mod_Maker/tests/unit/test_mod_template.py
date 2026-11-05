"""Pruebas unitarias para mod_template."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.mod_template import create_mod_template


def test_create_mod_template_creates_files(tmp_path: Path) -> None:
    target = tmp_path / "MiMod"
    create_mod_template(target, "MiMod", author="Autor", description="Un mod", factorio_version="2.0")
    assert (target / "info.json").exists()
    assert (target / "data.lua").exists()
    assert (target / "data-final-fixes.lua").exists()
    assert (target / "prototypes").is_dir()
    assert (target / "graphics").is_dir()
    assert (target / "locale").is_dir()


def test_create_mod_template_info_json_content(tmp_path: Path) -> None:
    target = tmp_path / "MiMod"
    create_mod_template(target, "MiMod", author="Autor", description="Desc", factorio_version="2.1")
    info = json.loads((target / "info.json").read_text(encoding="utf-8"))
    assert info["name"] == "MiMod"
    assert info["version"] == "1.0.0"
    assert info["author"] == "Autor"
    assert info["description"] == "Desc"
    assert info["factorio_version"] == "2.1"
    assert "base" in info["dependencies"]
