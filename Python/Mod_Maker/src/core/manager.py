"""Mod manager base de Mod_Maker.

Gestiona mods instalados por juego: listar, habilitar, deshabilitar, desinstalar.
"""

from __future__ import annotations

from pathlib import Path

from .plugin_system import PluginSystem

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)


class ModManager:
    """Gestiona los mods instalados de un juego concreto."""

    def __init__(self, plugin_system: PluginSystem, game_id: str = "factorio") -> None:
        self.plugin_system = plugin_system
        self.game_id = game_id
        self.plugin = plugin_system.get_plugin(game_id)
        if self.plugin is None:
            raise ValueError(f"No hay plugin cargado para el juego: {game_id}")

    def get_mods_folder(self) -> Path | None:
        """Devuelve la carpeta de mods del juego configurada o detectada."""
        folder = self.plugin.get_mods_folder()
        return Path(folder) if folder else None

    def list_installed_mods(self) -> list[Path]:
        """Lista los archivos de mod instalados en la carpeta del juego."""
        mods_folder = self.get_mods_folder()
        if mods_folder is None or not mods_folder.exists():
            return []
        extensions = self.plugin.supported_extensions
        return sorted(
            p for p in mods_folder.iterdir() if p.suffix.lower() in extensions
        )
