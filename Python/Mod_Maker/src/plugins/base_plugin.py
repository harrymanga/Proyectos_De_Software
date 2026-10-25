"""Clase base para plugins de juegos de Mod_Maker."""

from __future__ import annotations

from src.core.plugin_system import BasePlugin


class GamePlugin(BasePlugin):
    """Clase base conveniente para plugins de juegos concretos."""

    def detect_installation(self) -> str | None:
        raise NotImplementedError

    def get_mods_folder(self) -> str | None:
        raise NotImplementedError

    def extract(self, mod_path, dest_dir):
        raise NotImplementedError

    def build(self, source_dir, output_path):
        raise NotImplementedError

    def validate(self, mod_path):
        raise NotImplementedError

    def get_metadata(self, mod_path):
        raise NotImplementedError
