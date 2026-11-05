"""Adaptador de depuración base para mods de juegos.

Define la interfaz que todo adaptador de depuración debe implementar,
permitiendo depurar scripts de mods (Lua, JavaScript, etc.) desde la GUI
de Mod_Maker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class Breakpoint:
    """Representa un punto de interrupción en un archivo de código."""

    def __init__(self, file_path: str, line: int, condition: str | None = None) -> None:
        self.file_path = file_path
        self.line = line
        self.condition = condition
        self.enabled = True

    def __repr__(self) -> str:
        return f"Breakpoint({self.file_path}:{self.line})"


class DebugSession:
    """Representa una sesión de depuración activa."""

    def __init__(self, session_id: str, mod_path: Path) -> None:
        self.session_id = session_id
        self.mod_path = mod_path
        self.is_running = False
        self.is_paused = False
        self.current_line: int | None = None
        self.current_file: str | None = None
        self.variables: dict[str, Any] = {}
        self.output: list[str] = []
        self.breakpoints: list[Breakpoint] = []

    def add_output(self, text: str) -> None:
        """Agrega una línea de salida a la consola de depuración."""
        self.output.append(text)

    def set_variable(self, name: str, value: Any) -> None:
        """Establece el valor de una variable inspeccionada."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any | None:
        """Obtiene el valor de una variable inspeccionada."""
        return self.variables.get(name)


class DebugAdapter:
    """Interfaz base para adaptadores de depuración de mods."""

    def __init__(self, game_id: str) -> None:
        self.game_id = game_id
        self._sessions: dict[str, DebugSession] = {}

    def create_session(self, session_id: str, mod_path: Path) -> DebugSession:
        """Crea una nueva sesión de depuración para un mod."""
        session = DebugSession(session_id, mod_path)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> DebugSession | None:
        """Devuelve una sesión existente o None si no existe."""
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        """Elimina una sesión de depuración."""
        self._sessions.pop(session_id, None)

    def start(self, session_id: str) -> bool:
        """Inicia la depuración de una sesión."""
        raise NotImplementedError

    def pause(self, session_id: str) -> bool:
        """Pausa la ejecución de una sesión."""
        raise NotImplementedError

    def resume(self, session_id: str) -> bool:
        """Reanuda la ejecución de una sesión pausada."""
        raise NotImplementedError

    def stop(self, session_id: str) -> bool:
        """Detiene la depuración de una sesión."""
        raise NotImplementedError

    def set_breakpoint(self, session_id: str, file_path: str, line: int,
                       condition: str | None = None) -> bool:
        """Establece un punto de interrupción en una sesión."""
        raise NotImplementedError

    def remove_breakpoint(self, session_id: str, file_path: str,
                          line: int) -> bool:
        """Elimina un punto de interrupción de una sesión."""
        raise NotImplementedError

    def get_variables(self, session_id: str) -> dict[str, Any]:
        """Obtiene las variables inspeccionables de una sesión."""
        raise NotImplementedError

    def get_output(self, session_id: str) -> list[str]:
        """Obtiene la salida de consola de una sesión."""
        raise NotImplementedError

    def is_supported(self) -> bool:
        """Devuelve True si el adaptador de depuración está disponible."""
        raise NotImplementedError
