"""Depurador de Lua para mods de Factorio.

Provee una implementación base de DebugAdapter para scripts Lua de mods
de Factorio. Permite:

- Analizar archivos Lua y detectar líneas ejecutables.
- Establecer y eliminar puntos de interrupción.
- Capturar salida de consola (print) del mod.
- Inspeccionar variables globales de Lua.
- Infraestructura para conectarse a un debugger remoto (mobdebug) en
  fases futuras.

Nota: Esta implementación es una infraestructura base. La depuración en
tiempo real de mods de Factorio requiere el debugger integrado del juego
o una conexión remota vía mobdebug, que se agregará en fases posteriores.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.core.debug_adapter import Breakpoint, DebugAdapter
from src.core.logger import get_logger

logger = get_logger(__name__)


class LuaDebugAdapter(DebugAdapter):
    """Adaptador de depuración para scripts Lua de mods de Factorio."""

    def __init__(self) -> None:
        super().__init__("factorio")
        self._available = self._check_lua_available()

    def _check_lua_available(self) -> bool:
        """Verifica si hay un intérprete de Lua disponible en el sistema."""
        import shutil

        return shutil.which("lua") is not None or shutil.which("lua5.1") is not None

    def is_supported(self) -> bool:
        """Devuelve True si el adaptador de depuración Lua está disponible."""
        return self._available

    def start(self, session_id: str) -> bool:
        """Inicia la depuración de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None:
            return False

        if not session.mod_path.exists():
            session.add_output(f"Error: El mod no existe: {session.mod_path}")
            return False

        session.is_running = True
        session.is_paused = False
        session.add_output(f"Iniciando depuración de mod: {session.mod_path.name}")

        # Analizar archivos Lua del mod para detectar líneas ejecutables
        # Soporta tanto carpetas extraídas como archivos .zip
        lua_files: list[tuple[str, str]] = []  # (nombre_archivo, contenido_o_ruta)

        if session.mod_path.suffix.lower() == ".zip":
            # Leer archivos .lua dentro del ZIP
            import zipfile as zipfile_mod
            try:
                with zipfile_mod.ZipFile(session.mod_path, "r") as zip_ref:
                    for member in zip_ref.infolist():
                        if member.filename.endswith(".lua") and not member.is_dir():
                            try:
                                content = zip_ref.read(member.filename).decode(
                                    "utf-8", errors="replace"
                                )
                                lua_files.append((member.filename, content))
                            except Exception as exc:
                                logger.warning(
                                    "No se pudo leer %s del ZIP: %s",
                                    member.filename, exc,
                                )
                                continue
            except Exception as exc:
                session.add_output(f"Error leyendo ZIP: {exc}")
                return False
        else:
            # Carpeta extraída en disco
            for lua_file in sorted(session.mod_path.rglob("*.lua")):
                try:
                    content = lua_file.read_text(encoding="utf-8", errors="replace")
                    lua_files.append((str(lua_file), content))
                except Exception as exc:
                    logger.warning(
                        "No se pudo leer %s: %s", lua_file, exc
                    )
                    continue

        session.add_output(f"Archivos Lua detectados: {len(lua_files)}")

        for file_name, content in lua_files:
            executable_lines = self._get_executable_lines_from_content(content)
            if executable_lines:
                session.add_output(
                    f"  {file_name}: {len(executable_lines)} líneas ejecutables"
                )

        return True

    def pause(self, session_id: str) -> bool:
        """Pausa la ejecución de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None or not session.is_running:
            return False
        session.is_paused = True
        session.add_output("Depuración pausada")
        return True

    def resume(self, session_id: str) -> bool:
        """Reanuda la ejecución de una sesión Lua pausada."""
        session = self.get_session(session_id)
        if session is None or not session.is_paused:
            return False
        session.is_paused = False
        session.add_output("Depuración reanudada")
        return True

    def stop(self, session_id: str) -> bool:
        """Detiene la depuración de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None:
            return False
        session.is_running = False
        session.is_paused = False
        session.current_line = None
        session.current_file = None
        session.add_output("Depuración detenida")
        return True

    def set_breakpoint(self, session_id: str, file_path: str, line: int,
                       condition: str | None = None) -> bool:
        """Establece un punto de interrupción en un archivo Lua."""
        session = self.get_session(session_id)
        if session is None:
            return False

        # Verificar que la línea sea ejecutable en el archivo
        path = Path(file_path)
        if path.exists():
            executable = self._get_executable_lines(path)
            if line not in executable:
                session.add_output(
                    f"Advertencia: Línea {line} no ejecutable en {path.name}"
                )

        bp = Breakpoint(file_path, line, condition)
        session.breakpoints.append(bp)
        session.add_output(
            f"Breakpoint establecido: {Path(file_path).name}:{line}"
        )
        return True

    def remove_breakpoint(self, session_id: str, file_path: str,
                          line: int) -> bool:
        """Elimina un punto de interrupción de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None:
            return False

        for i, bp in enumerate(session.breakpoints):
            if bp.file_path == file_path and bp.line == line:
                session.breakpoints.pop(i)
                session.add_output(
                    f"Breakpoint eliminado: {Path(file_path).name}:{line}"
                )
                return True
        return False

    def get_variables(self, session_id: str) -> dict[str, Any]:
        """Obtiene las variables inspeccionables de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None:
            return {}
        return dict(session.variables)

    def get_output(self, session_id: str) -> list[str]:
        """Obtiene la salida de consola de una sesión Lua."""
        session = self.get_session(session_id)
        if session is None:
            return []
        return list(session.output)

    def _get_executable_lines(self, file_path: Path) -> list[int]:
        """Detecta líneas ejecutables en un archivo Lua.

        Una línea se considera ejecutable si contiene:
        - Declaraciones de función (function ... end)
        - Asignaciones (x = ...)
        - Llamadas a funciones
        - Estructuras de control (if, for, while, etc.)
        """
        executable_lines: list[int] = []

        try:
            with file_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return executable_lines

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignorar líneas vacías y comentarios
            if not stripped or stripped.startswith("--"):
                continue
            # Ignorar solo 'end' o 'then' solas (aunque son ejecutables,
            # son menos útiles como breakpoint)
            if stripped in ("end", "then", "else", "elseif", "until", "do"):
                continue
            # Detectar patrones ejecutables
            if re.search(r"\b(function|local\s+\w+\s*=|\w+\s*=\s*|if\s+|for\s+|while\s+|repeat\s+|print\s*\()", stripped):
                executable_lines.append(i)

        return executable_lines

    def _get_executable_lines_from_content(self, content: str) -> list[int]:
        """Detecta líneas ejecutables en contenido de texto Lua.

        Útil para archivos .lua leídos desde un ZIP.
        """
        executable_lines: list[int] = []
        lines = content.splitlines()

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignorar líneas vacías y comentarios
            if not stripped or stripped.startswith("--"):
                continue
            # Ignorar solo 'end' o 'then' solas
            if stripped in ("end", "then", "else", "elseif", "until", "do"):
                continue
            # Detectar patrones ejecutables
            if re.search(r"\b(function|local\s+\w+\s*=|\w+\s*=\s*|if\s+|for\s+|while\s+|repeat\s+|print\s*\()", stripped):
                executable_lines.append(i)

        return executable_lines

    def execute_lua_print(self, session_id: str, message: str) -> None:
        """Registra un mensaje de print de Lua en la salida de la sesión."""
        session = self.get_session(session_id)
        if session is not None:
            session.add_output(f"[Lua] {message}")

    def set_lua_variable(self, session_id: str, name: str, value: Any) -> None:
        """Establece una variable de Lua en la sesión para inspección."""
        session = self.get_session(session_id)
        if session is not None:
            session.set_variable(name, value)

    def remove_lua_variable(self, session_id: str, name: str) -> bool:
        """Elimina una variable de Lua de la sesión para inspección."""
        session = self.get_session(session_id)
        if session is not None:
            return session.variables.pop(name, None) is not None
        return False
