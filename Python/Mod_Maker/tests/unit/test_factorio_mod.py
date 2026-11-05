"""Pruebas unitarias para FactorioMod y modelos relacionados."""

from __future__ import annotations

from pathlib import Path

from src.core.factorio_mod import FactorioMod, ModMetadata, PrototypeItem, PrototypeTechnology
from src.core.prototype_generator import PrototypeGenerator


def test_mod_metadata_to_dict() -> None:
    meta = ModMetadata(name="TestMod", version="1.0.0", author="Autor", factorio_version="2.0")
    data = meta.to_dict()
    assert data["name"] == "TestMod"
    assert data["version"] == "1.0.0"
    assert data["factorio_version"] == "2.0"


def test_mod_metadata_from_dict() -> None:
    data = {"name": "Mod", "version": "2.0", "author": "A", "description": "D", "factorio_version": "2.1", "dependencies": ["base"], "homepage": ""}
    meta = ModMetadata.from_dict(data)
    assert meta.name == "Mod"
    assert meta.version == "2.0"
    assert meta.factorio_version == "2.1"


def test_prototype_item_to_lua() -> None:
    item = PrototypeItem(name="mi-item", stack_size=50, subgroup="intermediate-product")
    lua = item.to_lua()
    assert "mi-item" in lua
    assert "stack_size = 50" in lua
    assert 'subgroup = "intermediate-product"' in lua


def test_prototype_technology_to_lua() -> None:
    tech = PrototypeTechnology(name="mi-tecnologia", enabled=True, prerequisites=["base"])
    lua = tech.to_lua()
    assert "mi-tecnologia" in lua
    assert 'enabled = true' in lua


def test_factorio_mod_save_info_json(tmp_path: Path) -> None:
    mod = FactorioMod(
        metadata=ModMetadata(name="TestMod", version="1.0.0", factorio_version="2.0")
    )
    mod.save_info_json(tmp_path)
    info_file = tmp_path / "info.json"
    assert info_file.exists()
    content = info_file.read_text(encoding="utf-8")
    assert '"name": "TestMod"' in content
    assert '"version": "1.0.0"' in content


def test_factorio_mod_save_data_lua(tmp_path: Path) -> None:
    mod = FactorioMod(
        metadata=ModMetadata(name="TestMod", version="1.0.0")
    )
    mod.items.append(PrototypeItem(name="test-item", stack_size=10))
    mod.save_data_lua(tmp_path)
    data_file = tmp_path / "data.lua"
    assert data_file.exists()
    content = data_file.read_text(encoding="utf-8")
    assert "test-item" in content


def test_prototype_generator_add_item() -> None:
    gen = PrototypeGenerator(mod_name="MyMod")
    gen.add_item("item-1", stack_size=200)
    assert len(gen.items) == 1
    assert gen.items[0].name == "item-1"
    assert gen.items[0].stack_size == 200


def test_prototype_generator_add_technology() -> None:
    gen = PrototypeGenerator(mod_name="MyMod")
    gen.add_technology("tech-1", enabled=False, prerequisites=["base"])
    assert len(gen.technologies) == 1
    assert gen.technologies[0].name == "tech-1"
    assert gen.technologies[0].enabled is False


def test_prototype_generator_generate_lua() -> None:
    gen = PrototypeGenerator(mod_name="MyMod")
    gen.add_item("test-item")
    lua = gen.generate_lua()
    lua = gen.replace_mod_name_placeholder(lua)
    assert "test-item" in lua
    assert "__MOD_NAME__" not in lua
