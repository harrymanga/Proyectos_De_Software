"""Gestión de configuración de Mod_Maker.

Norma §13: configuración separada del código, sin valores mágicos,
sin rutas absolutas innecesarias, sin credenciales en el repositorio.
"""

from __future__ import annotations

import os
from pathlib import Path

import toml

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

CONFIG_FILE = Path.home() / ".mod_maker" / "config.toml"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "app": {
        "language": "es",
        "theme": "dark",
        "window_width": 1024,
        "window_height": 768,
    },
    "games": {
        "factorio": {
            "enabled": True,
            "mods_folder": "",  # Se detecta automáticamente por SO si está vacío
        },
    },
    "security": {
        "allow_path_traversal": False,
        "max_extract_size_mb": 500,
    },
}


class ConfigManager:
    """Carga y guarda la configuración en un archivo TOML.

    Los valores por defecto se aplican cuando falta una clave.
    """

    def __init__(self, config_file: Path | None = None) -> None:
        self.config_file = config_file or CONFIG_FILE
        self._config: dict = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self) -> None:
        if self.config_file.exists():
            try:
                with self.config_file.open("r", encoding="utf-8") as f:
                    file_config = toml.load(f)
                self._merge(self._config, file_config)
                logger.info("Configuración cargada desde %s", self.config_file)
            except Exception as exc:  # pragma: no cover - defensivo
                logger.warning("No se pudo cargar la configuración: %s", exc)
        else:
            self._save()
            logger.info("Archivo de configuración creado en %s", self.config_file)

    @staticmethod
    def _merge(base: dict, override: dict) -> None:
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ConfigManager._merge(base[key], value)
            else:
                base[key] = value

    def _save(self) -> None:
        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                toml.dump(self._config, f)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("No se pudo guardar la configuración: %s", exc)

    def get(self, section: str, key: str, default=None):
        """Devuelve un valor de configuración."""
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value) -> None:
        """Establece un valor de configuración y lo guarda en disco."""
        self._config.setdefault(section, {})[key] = value
        self._save()

    def get_games(self) -> dict:
        """Devuelve la sección de juegos."""
        return self._config.get("games", {})

    def get_factorio_mods_folder(self) -> str | None:
        """Devuelve la carpeta de mods de Factorio configurada, si existe."""
        return self.get("games", "factorio", {}).get("mods_folder") or None
