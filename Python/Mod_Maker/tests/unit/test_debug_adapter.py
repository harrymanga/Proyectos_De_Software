"""Pruebas unitarias para el adaptador de depuración base."""

from __future__ import annotations

from pathlib import Path

from src.core.debug_adapter import Breakpoint, DebugAdapter, DebugSession


class ConcreteDebugAdapter(DebugAdapter):
    """Implementación concreta para pruebas."""

    def __init__(self) -> None:
        super().__init__("test_game")
        self.started = False
        self.paused = False
        self.resumed = False
        self.stopped = False

    def is_supported(self) -> bool:
        return True

    def start(self, session_id: str) -> bool:
        self.started = True
        return True

    def pause(self, session_id: str) -> bool:
        self.paused = True
        return True

    def resume(self, session_id: str) -> bool:
        self.resumed = True
        return True

    def stop(self, session_id: str) -> bool:
        self.stopped = True
        return True

    def set_breakpoint(self, session_id: str, file_path: str, line: int,
                       condition: str | None = None) -> bool:
        return True

    def remove_breakpoint(self, session_id: str, file_path: str,
                          line: int) -> bool:
        return True

    def get_variables(self, session_id: str) -> dict:
        return {}

    def get_output(self, session_id: str) -> list[str]:
        return []


def test_debug_session_creation() -> None:
    """Una sesión de depuración debe crearse con los campos correctos."""
    mod_path = Path("/tmp/test_mod")
    session = DebugSession("session_1", mod_path)

    assert session.session_id == "session_1"
    assert session.mod_path == mod_path
    assert session.is_running is False
    assert session.is_paused is False
    assert session.current_line is None
    assert session.current_file is None
    assert session.variables == {}
    assert session.output == []
    assert session.breakpoints == []


def test_debug_session_add_output() -> None:
    """add_output debe agregar texto a la salida de la sesión."""
    session = DebugSession("s", Path("/tmp"))
    session.add_output("Hola depuración")
    assert session.output == ["Hola depuración"]


def test_debug_session_set_variable() -> None:
    """set_variable y get_variable deben almacenar y recuperar valores."""
    session = DebugSession("s", Path("/tmp"))
    session.set_variable("x", 42)
    session.set_variable("nombre", "mod_test")

    assert session.get_variable("x") == 42
    assert session.get_variable("nombre") == "mod_test"
    assert session.get_variable("inexistente") is None


def test_breakpoint_creation() -> None:
    """Un breakpoint debe almacenar archivo, línea y condición opcional."""
    bp = Breakpoint("/tmp/mod/data.lua", 42, "x > 10")

    assert bp.file_path == "/tmp/mod/data.lua"
    assert bp.line == 42
    assert bp.condition == "x > 10"
    assert bp.enabled is True


def test_debug_adapter_create_and_get_session() -> None:
    """El adaptador debe crear y recuperar sesiones correctamente."""
    adapter = ConcreteDebugAdapter()
    mod_path = Path("/tmp/test_mod")
    session = adapter.create_session("s1", mod_path)

    assert session is not None
    assert adapter.get_session("s1") is session
    assert adapter.get_session("inexistente") is None


def test_debug_adapter_remove_session() -> None:
    """remove_session debe eliminar la sesión del adaptador."""
    adapter = ConcreteDebugAdapter()
    adapter.create_session("s1", Path("/tmp"))
    adapter.remove_session("s1")

    assert adapter.get_session("s1") is None


def test_debug_adapter_subclass_methods() -> None:
    """Los métodos de la subclase concreta deben marcar las banderas correctas."""
    adapter = ConcreteDebugAdapter()
    adapter.create_session("s1", Path("/tmp"))

    assert adapter.start("s1") is True
    assert adapter.started is True

    assert adapter.pause("s1") is True
    assert adapter.paused is True

    assert adapter.resume("s1") is True
    assert adapter.resumed is True

    assert adapter.stop("s1") is True
    assert adapter.stopped is True
