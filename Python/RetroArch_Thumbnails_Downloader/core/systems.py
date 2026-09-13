"""Carga y consulta de sistemas (data/systems.json) con caché."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from core.resources import get_resource_path

FALLBACK_EXTENSIONS: List[str] = [".nes", ".sfc", ".smc", ".gba", ".nds", ".iso", ".bin"]


@lru_cache(maxsize=1)
def load_systems_raw() -> Dict[str, str]:
    path = get_resource_path("data/systems.json")
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def expand_systems(systems: Dict[str, str]) -> Dict[str, str]:
    expanded: Dict[str, str] = {}
    for key, value in systems.items():
        if "," in key:
            for ext in (e.strip().lower() for e in key.split(",")):
                if ext:
                    expanded[ext] = value
        else:
            expanded[key.strip().lower()] = value
    return expanded


@lru_cache(maxsize=1)
def load_expanded_systems() -> Dict[str, str]:
    return expand_systems(load_systems_raw())


def list_extensions() -> List[str]:
    exts = list(load_expanded_systems().keys())
    return exts or list(FALLBACK_EXTENSIONS)


def list_system_names() -> List[str]:
    return list(dict.fromkeys(load_systems_raw().values()))


def detect_system(file: str | Path | None) -> Optional[str]:
    if not file:
        return None
    ext = Path(str(file)).suffix.lower()
    if not ext:
        return None
    return load_expanded_systems().get(ext)


def validate_system_extension(file: str | Path | None, system: str | None) -> bool:
    if not file or not system:
        return False
    ext = Path(str(file)).suffix.lower()
    for key, value in load_systems_raw().items():
        if value != system:
            continue
        if ext in [e.strip().lower() for e in key.split(",")]:
            return True
    return False
