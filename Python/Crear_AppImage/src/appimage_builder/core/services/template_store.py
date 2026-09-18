"""Plantillas de configuración guardadas (`~/.config/appimage-builder/templates/`)."""

from __future__ import annotations

import re
from pathlib import Path

from appimage_builder.core.exceptions import ConfigurationError
from appimage_builder.core.models import AppImageBuilderConfig

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def default_templates_dir() -> Path:
    return Path.home() / ".config" / "appimage-builder" / "templates"


class TemplateStore:
    """Guarda/carga `AppImageBuilderConfig` como plantillas TOML nombradas."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory.expanduser().resolve() if directory else default_templates_dir()
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def check_name(name: str) -> str:
        name = name.strip()
        if not _NAME_PATTERN.match(name):
            raise ConfigurationError(
                f"Nombre de plantilla inválido: {name!r}.",
                hint="Usa alfanuméricos, ., _ y - (empieza con alfanumérico).",
            )
        return name

    def _path(self, name: str) -> Path:
        return self.directory / f"{self.check_name(name)}.toml"

    def save(self, name: str, config: AppImageBuilderConfig) -> Path:
        """Guarda (sobrescribe) y devuelve la ruta del archivo."""
        import tomli_w

        dest = self._path(name)
        with dest.open("wb") as f:
            tomli_w.dump(config.model_dump(mode="json", exclude_none=True), f)
        return dest

    def load(self, name: str) -> AppImageBuilderConfig:
        """Carga una plantilla. Lanza ConfigurationError si no existe o es inválida."""
        import tomllib

        path = self._path(name)
        if not path.exists():
            raise ConfigurationError(
                f"Plantilla no encontrada: {name!r}.",
                config_path=path,
                hint=f"Disponibles: {', '.join(self.list_names()) or '(ninguna)'}.",
            )
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            return AppImageBuilderConfig.model_validate(data)
        except Exception as e:
            raise ConfigurationError(
                f"Plantilla inválida: {name!r}.",
                config_path=path,
                hint=f"Verifica la sintaxis TOML: {e}",
            ) from e

    def list_names(self) -> list[str]:
        try:
            names = sorted(p.stem for p in self.directory.glob("*.toml") if p.is_file())
        except OSError:
            return []
        return [n for n in names if _NAME_PATTERN.match(n)]

    def delete(self, name: str) -> None:
        path = self._path(name)
        if not path.exists():
            raise ConfigurationError(f"Plantilla no encontrada: {name!r}.", config_path=path)
        path.unlink()
