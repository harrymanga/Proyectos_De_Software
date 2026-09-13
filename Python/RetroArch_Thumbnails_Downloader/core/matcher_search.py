#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Búsqueda de coincidencias alternativas en thumbnails.libretro.com."""
from __future__ import annotations

import re
import urllib.parse
from typing import List, Tuple
from urllib.parse import quote

import requests

from core import logger as log
from core.http import get_session
from core.matcher import normalize_for_search

TIMEOUT = 10
_HREF_RE = re.compile(r'<a href="([^"]+\.png)">')
REGIONS = ["(USA)", "(Europe)", "(Japan)", "(World)", "(USA, Europe)", "(En,Fr,De,Es,It)"]


def search_matches(
    system: str, base_name: str, art_type: str = "Named_Boxarts"
) -> List[Tuple[str, str]]:
    try:
        system_url = f"https://thumbnails.libretro.com/{quote(system, safe='')}/{art_type}/"
        response = get_session().get(system_url, timeout=TIMEOUT)
        if response.status_code != 200:
            return []

        matches = _HREF_RE.findall(response.text)
        base_normalized = normalize_for_search(base_name)
        found: List[Tuple[str, str]] = []
        for match in matches:
            decoded = urllib.parse.unquote(match.removesuffix(".png"))
            match_normalized = normalize_for_search(decoded)
            if base_normalized in match_normalized or match_normalized in base_normalized:
                found.append((decoded, f"{system_url}{match}"))
        return found
    except requests.RequestException as e:
        log.error(f"Error buscando coincidencias: {e}")
        return []
    except Exception as e:  # noqa: BLE001 - red resiliente
        log.error(f"Error inesperado buscando coincidencias: {e}")
        return []


def get_variants(
    base_name: str, system: str, art_type: str = "Named_Boxarts"
) -> List[Tuple[str, str]]:
    variants = [base_name, *(f"{base_name} {r}" for r in REGIONS)]
    return [
        (
            v,
            f"https://thumbnails.libretro.com/{quote(system, safe='')}/{art_type}/{quote(v, safe='')}.png",
        )
        for v in variants
    ]
