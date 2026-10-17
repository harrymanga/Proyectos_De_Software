"""Localiza makeself y verifica dependencias. backends/deps.py"""
from __future__ import annotations

import shutil

REQUIRED = ["bash", "tar"]
COMPRESSORS = {
    "gzip": "gzip",
    "xz": "xz",
    "zstd": "zstd",
    "bzip2": "bzip2",
    "lzo": "lzop",
    "lz4": "lz4",
}


def find_makeself() -> str | None:
    return shutil.which("makeself")


def check_deps() -> dict[str, bool]:
    out = {cmd: shutil.which(cmd) is not None for cmd in REQUIRED}
    out["makeself"] = find_makeself() is not None
    for name, bin_ in COMPRESSORS.items():
        out[f"comp:{name}"] = shutil.which(bin_) is not None
    return out
