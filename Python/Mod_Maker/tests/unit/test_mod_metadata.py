"""Pruebas unitarias para ModMetadata."""

from __future__ import annotations

from src.core.mod import ModMetadata


def test_mod_metadata_to_dict() -> None:
    meta = ModMetadata(
        name="MiMod",
        version="1.0.0",
        author="Autor",
        description="Un mod de prueba",
        factorio_version="1.1",
        dependencies=["base"],
    )
    data = meta.to_dict()
    assert data["name"] == "MiMod"
    assert data["version"] == "1.0.0"
    assert data["dependencies"] == ["base"]


def test_mod_metadata_from_dict() -> None:
    data = {
        "name": "OtroMod",
        "version": "2.0",
        "author": "Otro",
        "description": "",
        "factorio_version": "1.1",
        "dependencies": [],
        "homepage": "",
    }
    meta = ModMetadata.from_dict(data)
    assert meta.name == "OtroMod"
    assert meta.version == "2.0"
