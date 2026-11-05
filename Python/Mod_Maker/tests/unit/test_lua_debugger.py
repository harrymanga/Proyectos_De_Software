"""Pruebas unitarias para el depurador de Lua (LuaDebugAdapter)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.lua_debugger import LuaDebugAdapter


@pytest.fixture
def lua_adapter() -> LuaDebugAdapter:
    """Provee una instancia de LuaDebugAdapter para pruebas."""
    return LuaDebugAdapter()


def test_lua_debugger_is_supported(lua_adapter: LuaDebugAdapter) -> None:
    """is_supported debe devolver un booleano."""
    assert isinstance(lua_adapter.is_supported(), bool)


def test_lua_debugger_game_id(lua_adapter: LuaDebugAdapter) -> None:
    """El game_id debe ser 'factorio'."""
    assert lua_adapter.game_id == "factorio"


def test_lua_debugger_create_session(lua_adapter: LuaDebugAdapter) -> None:
    """create_session debe crear una sesión válida."""
    session = lua_adapter.create_session("s1", Path("/tmp/test_mod"))

    assert session is not None
    assert session.session_id == "s1"
    assert session.mod_path == Path("/tmp/test_mod")
    assert lua_adapter.get_session("s1") is session


def test_lua_debugger_get_nonexistent_session(lua_adapter: LuaDebugAdapter) -> None:
    """get_session debe devolver None para sesiones inexistentes."""
    assert lua_adapter.get_session("inexistente") is None


def test_lua_debugger_start_stop_session(lua_adapter: LuaDebugAdapter,
                                          tmp_path: Path) -> None:
    """start y stop deben cambiar el estado de la sesión."""
    mod_dir = tmp_path / "test_mod"
    mod_dir.mkdir()
    session = lua_adapter.create_session("s1", mod_dir)

    assert lua_adapter.start("s1") is True
    assert session.is_running is True

    assert lua_adapter.stop("s1") is True
    assert session.is_running is False


def test_lua_debugger_pause_resume(lua_adapter: LuaDebugAdapter,
                                    tmp_path: Path) -> None:
    """pause y resume deben cambiar el estado de pausa."""
    mod_dir = tmp_path / "test_mod"
    mod_dir.mkdir()
    session = lua_adapter.create_session("s1", mod_dir)
    lua_adapter.start("s1")

    assert lua_adapter.pause("s1") is True
    assert session.is_paused is True

    assert lua_adapter.resume("s1") is True
    assert session.is_paused is False


def test_lua_debugger_set_and_remove_breakpoint(
    lua_adapter: LuaDebugAdapter, tmp_path: Path
) -> None:
    """set_breakpoint y remove_breakpoint deben gestionar breakpoints."""
    session = lua_adapter.create_session("s1", tmp_path)

    # Crear un archivo Lua de prueba
    lua_file = tmp_path / "data.lua"
    lua_file.write_text('print("hola")\nx = 1\nfunction foo()\nend\n', encoding="utf-8")

    assert lua_adapter.set_breakpoint("s1", str(lua_file), 1) is True
    assert len(session.breakpoints) == 1
    assert session.breakpoints[0].line == 1

    assert lua_adapter.remove_breakpoint("s1", str(lua_file), 1) is True
    assert len(session.breakpoints) == 0


def test_lua_debugger_get_output(lua_adapter: LuaDebugAdapter) -> None:
    """get_output debe devolver las líneas de salida de la sesión."""
    session = lua_adapter.create_session("s1", Path("/tmp/test_mod"))
    session.add_output("Lua output line 1")
    session.add_output("Lua output line 2")

    output = lua_adapter.get_output("s1")
    assert output == ["Lua output line 1", "Lua output line 2"]


def test_lua_debugger_variables(lua_adapter: LuaDebugAdapter) -> None:
    """set_lua_variable y get_variables deben almacenar variables."""
    lua_adapter.create_session("s1", Path("/tmp/test_mod"))

    lua_adapter.set_lua_variable("s1", "x", 42)
    lua_adapter.set_lua_variable("s1", "nombre", "mi_mod")

    variables = lua_adapter.get_variables("s1")
    assert variables["x"] == 42
    assert variables["nombre"] == "mi_mod"


def test_lua_debugger_get_executable_lines(tmp_path: Path) -> None:
    """_get_executable_lines debe detectar líneas ejecutables en un archivo Lua."""
    lua_adapter = LuaDebugAdapter()

    lua_file = tmp_path / "test.lua"
    lua_file.write_text(
        "-- comentario\n"
        "print(\"hola\")\n"
        "x = 10\n"
        "if x > 5 then\n"
        "    print(\"mayor\")\n"
        "end\n"
        "function foo()\n"
        "    return 1\n"
        "end\n",
        encoding="utf-8",
    )

    lines = lua_adapter._get_executable_lines(lua_file)
    assert 2 in lines   # print("hola")
    assert 3 in lines   # x = 10
    assert 4 in lines   # if x > 5 then
    assert 5 in lines   #     print("mayor")
    assert 7 in lines   # function foo()


def test_lua_debugger_get_executable_lines_ignores_comments(
    lua_adapter: LuaDebugAdapter, tmp_path: Path
) -> None:
    """Las líneas de comentario no deben considerarse ejecutables."""
    lua_file = tmp_path / "test.lua"
    lua_file.write_text(
        "-- esto es un comentario\n"
        "-- otro comentario\n"
        "print(\"real\")\n",
        encoding="utf-8",
    )

    lines = lua_adapter._get_executable_lines(lua_file)
    assert 1 not in lines
    assert 2 not in lines
    assert 3 in lines


def test_lua_debugger_execute_lua_print(
    lua_adapter: LuaDebugAdapter
) -> None:
    """execute_lua_print debe agregar un mensaje a la salida de la sesión."""
    lua_adapter.create_session("s1", Path("/tmp/test_mod"))

    lua_adapter.execute_lua_print("s1", "Mensaje desde Lua")
    output = lua_adapter.get_output("s1")

    assert any("Mensaje desde Lua" in line for line in output)
