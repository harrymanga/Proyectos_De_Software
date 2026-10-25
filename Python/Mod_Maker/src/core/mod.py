"""Modelo de datos de un mod de Mod_Maker."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModMetadata:
    """Metadatos de un mod (equivalente a info.json de Factorio)."""

    name: str
    version: str
    author: str = ""
    description: str = ""
    factorio_version: str = ""
    dependencies: list[str] = field(default_factory=list)
    homepage: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "factorio_version": self.factorio_version,
            "dependencies": self.dependencies,
            "homepage": self.homepage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModMetadata":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", ""),
            author=data.get("author", ""),
            description=data.get("description", ""),
            factorio_version=data.get("factorio_version", ""),
            dependencies=data.get("dependencies", []),
            homepage=data.get("homepage", ""),
        )


@dataclass
class Mod:
    """Representa un mod instalado o en proceso de creación."""

    metadata: ModMetadata
    path: Path
    enabled: bool = True
    installed: bool = False

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version
