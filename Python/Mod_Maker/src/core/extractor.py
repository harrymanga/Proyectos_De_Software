"""Interfaz de extracción de mods del núcleo.

Orquesta la extracción usando el plugin correspondiente al juego.
"""

from __future__ import annotations

from pathlib import Path

from .plugin_system import BasePlugin, PluginSystem
from .security import SecurityError, validate_extraction_target

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)


class Extractor:
    """Extrae el contenido de un mod usando el plugin del juego."""

    def __init__(self, plugin_system: PluginSystem) -> None:
        self.plugin_system = plugin_system

    def extract(self, mod_path: Path, dest_dir: Path, game_id: str = "factorio") -> None:
        """Extrae mod_path a dest_dir usando el plugin de game_id."""
        plugin = self.plugin_system.get_plugin(game_id)
        if plugin is None:
            raise ValueError(f"No hay plugin cargado para el juego: {game_id}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Extrayendo mod %s a %s", mod_path, dest_dir)
        plugin.extract(mod_path, dest_dir)
