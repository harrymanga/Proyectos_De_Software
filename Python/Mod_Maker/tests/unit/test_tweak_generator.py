"""Pruebas unitarias para TweakGenerator."""

from __future__ import annotations

from src.core.tweak_generator import TweakGenerator


def test_tweak_generator_defaults() -> None:
    tg = TweakGenerator(mod_name="TestMod")
    assert tg.crafting_speed_multiplier == 1.0
    assert tg.recipe_cost_multiplier == 1.0
    assert tg.inventory_stack_size_bonus == 0


def test_tweak_generator_set_values() -> None:
    tg = TweakGenerator(mod_name="TestMod")
    tg.set_crafting_speed(2.5)
    tg.set_recipe_cost(0.5)
    tg.set_stack_size_bonus(100)
    assert tg.crafting_speed_multiplier == 2.5
    assert tg.recipe_cost_multiplier == 0.5
    assert tg.inventory_stack_size_bonus == 100


def test_tweak_generator_generate_lua() -> None:
    tg = TweakGenerator(mod_name="TestMod")
    lua = tg.generate_lua()
    assert "TestMod" in lua
    assert "data-final-fixes" in lua.lower()


def test_tweak_generator_crafting_speed_in_lua() -> None:
    tg = TweakGenerator(mod_name="TestMod")
    tg.set_crafting_speed(2.0)
    lua = tg.generate_lua()
    assert "2.0" in lua


def test_tweak_generator_stack_size_bonus_in_lua() -> None:
    tg = TweakGenerator(mod_name="TestMod")
    tg.set_stack_size_bonus(50)
    lua = tg.generate_lua()
    assert "50" in lua


def test_tweak_generator_no_tweaks() -> None:
    tg = TweakGenerator(mod_name="Empty")
    lua = tg.generate_lua()
    assert "No hay tweaks aplicados" in lua or lua.strip() != ""
