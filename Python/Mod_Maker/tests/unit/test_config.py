"""Pruebas unitarias para ConfigManager."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.core.config import ConfigManager, DEFAULT_CONFIG


def test_default_config_values() -> None:
    """Los valores por defecto deben estar presentes."""
    assert DEFAULT_CONFIG["app"]["language"] == "es"
    assert DEFAULT_CONFIG["app"]["theme"] == "dark"


def test_config_load_and_save(tmp_path: Path) -> None:
    """La configuración se carga y guarda correctamente."""
    config_file = tmp_path / "config.toml"
    cm = ConfigManager(config_file=config_file)
    cm.set("app", "language", "en")
    assert cm.get("app", "language") == "en"

    # Recargar desde disco
    cm2 = ConfigManager(config_file=config_file)
    assert cm2.get("app", "language") == "en"


def test_config_missing_file_creates_default(tmp_path: Path) -> None:
    """Si falta el archivo, se crea con valores por defecto."""
    config_file = tmp_path / "new_config.toml"
    cm = ConfigManager(config_file=config_file)
    assert config_file.exists()
    assert cm.get("app", "language") == DEFAULT_CONFIG["app"]["language"]
