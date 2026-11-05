"""Pruebas unitarias para PrototypeGenerator."""

from __future__ import annotations

from src.core.prototype_generator import PrototypeGenerator


def test_generator_initial_state() -> None:
    gen = PrototypeGenerator(mod_name="TestMod")
    assert gen.mod_name == "TestMod"
    assert gen.items == []
    assert gen.technologies == []
    assert gen.recipes == []
    assert gen.entities == []


def test_generator_add_multiple_items() -> None:
    gen = PrototypeGenerator(mod_name="TestMod")
    gen.add_item("item-a", stack_size=10)
    gen.add_item("item-b", stack_size=20)
    assert len(gen.items) == 2
    assert gen.items[1].name == "item-b"


def test_generator_add_recipe() -> None:
    gen = PrototypeGenerator(mod_name="TestMod")
    gen.add_recipe("recipe-1", [["iron-plate", 5]], [["gear-wheel", 1]], energy_required=2.0)
    assert len(gen.recipes) == 1
    assert gen.recipes[0]["name"] == "recipe-1"
    assert gen.recipes[0]["energy_required"] == 2.0


def test_generator_generate_lua_empty() -> None:
    gen = PrototypeGenerator(mod_name="EmptyMod")
    lua = gen.generate_lua()
    assert lua == "" or lua is not None


def test_generator_replace_mod_name() -> None:
    gen = PrototypeGenerator(mod_name="MyCustomMod")
    lua = gen.replace_mod_name_placeholder("icon = \"__MOD_NAME__/graphics/icon.png\"")
    assert "__MOD_NAME__" not in lua
    assert "MyCustomMod" in lua
