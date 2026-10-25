"""Sistema de plugins de Mod_Maker.

Permite descubrir, cargar y descargar plugins de soporte por juego.
El núcleo no depende de plugins; los plugins dependen del núcleo.
Norma §10: dependencias acíclicas.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

PLUGINS_DIR = Path(__file__).resolve().parents[1] / "plugins"


class BasePlugin:
    """Clase base que todo plugin de juego debe implementar."""

    game_id: str = ""
    game_name: str = ""
    supported_extensions: tuple[str, ...] = (".zip",)

    def detect_installation(self) -> str | None:
        """Devuelve la ruta de instalación del juego, o None si no se encuentra."""
        raise NotImplementedError

    def get_mods_folder(self) -> str | None:
        """Devuelve la carpeta de mods del juego, o None si no se puede determinar."""
        raise NotImplementedError

    def set_mods_folder(self, folder_path: str) -> None:
        """Establece manualmente la carpeta de mods del juego.

        Los plugins pueden sobrescribir este método para soportar
        configuración de ruta personalizada cuando la detección automática
        falla.
        """
        raise NotImplementedError(
            f"El plugin {self.game_id} no soporta configuración de ruta personalizada"
        )

    def extract(self, mod_path: Path, dest_dir: Path) -> None:
        """Extrae el contenido de un mod a una carpeta de destino."""
        raise NotImplementedError

    def build(self, source_dir: Path, output_path: Path) -> None:
        """Reempaqueta una carpeta de origen como un mod válido."""
        raise NotImplementedError

    def validate(self, mod_path: Path) -> bool:
        """Valida que un archivo sea un mod válido para este juego."""
        raise NotImplementedError

    def get_metadata(self, mod_path: Path) -> dict | None:
        """Lee los metadatos de un mod."""
        raise NotImplementedError


class PluginSystem:
    """Descubre y gestiona plugins de juegos."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self._plugins: dict[str, BasePlugin] = {}
        self._load_plugins()

    def _load_plugins(self) -> None:
        if not self.plugins_dir.exists():
            logger.warning("Directorio de plugins no encontrado: %s", self.plugins_dir)
            return
        for plugin_dir in sorted(self.plugins_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                continue
            module_name = f"src.plugins.{plugin_dir.name}"
            try:
                module = importlib.import_module(module_name)
                plugin = self._instantiate_plugin(module)
                if plugin:
                    self._plugins[plugin.game_id] = plugin
                    logger.info("Plugin cargado: %s (%s)", plugin.game_name, plugin.game_id)
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("No se pudo cargar el plugin %s: %s", plugin_dir.name, exc)

    @staticmethod
    def _instantiate_plugin(module: ModuleType) -> BasePlugin | None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePlugin)
                and attr is not BasePlugin
            ):
                return attr()
        return None

    def get_plugin(self, game_id: str) -> BasePlugin | None:
        """Devuelve el plugin para el juego dado, o None si no existe."""
        return self._plugins.get(game_id)

    def list_plugins(self) -> list[str]:
        """Devuelve los IDs de juegos con plugin cargado."""
        return sorted(self._plugins.keys())

    def get_game_folder(self, game_id: str) -> str | None:
        """Devuelve la carpeta de mods para un juego.

        Primero verifica si existe una ruta personalizada configurada por el usuario.
        Si no, consulta al plugin del juego mediante su detección automática.
        """
        plugin = self._plugins.get(game_id)
        if plugin is None:
            return None
        return plugin.get_mods_folder()

    def set_game_folder(self, game_id: str, folder_path: str) -> None:
        """Establece manualmente la carpeta de mods para un juego.

        Se usa cuando la detección automática falla y el usuario proporciona
        una ubicación personalizada. Funciona para cualquier plugin que
        implemente set_mods_folder.
        """
        plugin = self._plugins.get(game_id)
        if plugin is None:
            raise ValueError(f"No hay plugin cargado para el juego: {game_id}")
        plugin.set_mods_folder(folder_path)
