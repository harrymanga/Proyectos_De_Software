"""Utilidad pura para extraer porcentaje de las líneas de makeself."""
from __future__ import annotations

import os
import re

_PERCENT = re.compile(r"(\d{1,3})%")
# MojoSetup: "archivo: 43% (total progress: 8%)"
_MOJO_TOTAL = re.compile(r"total progress:\s*(\d{1,3})%")
_MOJO_FILE = re.compile(r"([^\r\n()]+?):\s*\d{1,3}%\s*\(")


def find_percent(line: str) -> int | None:
    """Devuelve el último N de 'N%' en la línea, limitado a 0-100, o None."""
    matches = _PERCENT.findall(line or "")
    if not matches:
        return None
    return max(0, min(100, int(matches[-1])))


def clean_output(text: str) -> str:
    """Emula terminal para \b y \r para que el log no muestre basura.

    Makeself reescribe la misma línea con backspaces (63% \b\b\b 64%…).
    Se procesa carácter a carácter y se colapsan espacios repetidos.
    """
    out: list[str] = []
    for char in text or "":
        if char == "\x08":
            if out:
                out.pop()
        elif char == "\r":
            while out and out[-1] != "\n":
                out.pop()
        else:
            out.append(char)
    cleaned = re.sub(r"[ \t]{2,}", " ", "".join(out))
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


_PHASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sha256", ("sha256",)),
    ("md5", ("md5",)),
    ("crc", ("crc",)),
    ("verify", ("verifying", "integrity")),
    ("extract", ("uncompressing",)),
    ("compress", ("compress", "adding files")),
)


def find_total_percent(line: str) -> int | None:
    """Extrae el progreso global de MojoSetup: 'f1.bin: 43% (total progress: 8%)'."""
    match = _MOJO_TOTAL.search(line or "")
    if not match:
        return None
    return max(0, min(100, int(match.group(1))))


def find_current_file(line: str) -> str | None:
    """Nombre del archivo que MojoSetup está instalando en esa línea."""
    match = _MOJO_FILE.search(line or "")
    return match.group(1) if match else None


def detect_phase(block: str) -> str | None:
    """Detecta qué verifica/comprime makeself en ese fragmento.

    Devuelve clave de fase (crc/sha256/md5/verify/extract/compress) o None.
    """
    lowered = (block or "").lower()
    for key, keywords in _PHASES:
        if any(word in lowered for word in keywords):
            return key
    return None


_TAR_ENTRY = re.compile(r"^(?:a )?\./.*\n", re.MULTILINE)


def count_tar_entries(block: str) -> int:
    """Cuenta archivos archivados por tar en el fragmento.

    Cubre bsdtar (`a ./x`) y GNU tar (`./x`), que es lo que imprime
    makeself al crear (no emite % en esa fase).
    """
    return len(_TAR_ENTRY.findall(block or ""))


def count_files(root: str) -> int:
    """Cuenta archivos (no directorios) bajo root para el total de progreso."""
    total = 0
    for _dir, _subdirs, files in os.walk(root):
        total += len(files)
    return total
