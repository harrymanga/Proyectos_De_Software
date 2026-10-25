"""Interfaz de reconstrucción/empaquetado de mods del núcleo.

Orquesta la construcción usando el plugin correspondiente al juego.
"""

from __future__ import annotations

from pathlib import Path

from .plugin_system import BasePlugin, PluginSystem

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)


class Builder:
    """Reempaqueta una carpeta de origen como un mod válido usando el plugin del juego."""

    def __init__(self, plugin_system: PluginSystem) -> None:
        self.plugin_system = plugin_system

    def build(
        self,
        source_dir: Path,
        output_path: Path,
        game_id: str = "factorio",
    ) -> None:
        """Construye un mod en output_path a partir de source_dir."""
        plugin = self.plugin_system.get_plugin(game_id)
        if plugin is None:
            raise ValueError(f"No hay plugin cargado para el juego: {game_id}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Construyendo mod desde %s en %s", source_dir, output_path)
        plugin.build(source_dir, output_path)
