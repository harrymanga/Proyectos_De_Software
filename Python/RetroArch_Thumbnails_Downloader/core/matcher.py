"""Normalización de nombres de ROM a formato LibRetro."""
from __future__ import annotations

import re
import urllib.parse
from pathlib import Path
from typing import Optional

_BRACKETS_RE = re.compile(r"\[.*?\]")
_CLEAN_RE = re.compile(r"[^a-zA-Z0-9\s\(\)\-\_\#\.]")
_SPACES_RE = re.compile(r"\s+")


def normalize(name: str | Path | None) -> Optional[str]:
    if not name:
        return None
    basename = Path(str(name)).stem
    text = basename.strip()
    if not text:
        return None
    text = _BRACKETS_RE.sub("", text)
    text = _CLEAN_RE.sub(" ", text)
    text = _SPACES_RE.sub(" ", text).strip()
    if not text:
        return None
    return urllib.parse.quote(text, safe="")


def normalize_for_search(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "").replace("_", "")
