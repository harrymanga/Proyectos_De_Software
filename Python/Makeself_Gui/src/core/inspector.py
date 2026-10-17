"""Inspección segura de .run sin ejecutar payload. core/inspector.py"""
from __future__ import annotations

import os
import re
import subprocess


def suggest_extract_dir(run_path: str) -> str:
    """Carpeta destino a partir del nombre del .sh/.run, evitando colisiones.

    Ej: /juegos/mi-juego.sh -> /juegos/mi-juego-extracted (o -extracted-1...).
    """
    base = os.path.basename(run_path)
    for ext in (".sh", ".run"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break
    stem = base.strip() or "extraido"
    parent = os.path.dirname(os.path.abspath(run_path)) or "/tmp"
    candidate = os.path.join(parent, f"{stem}-extracted")
    index = 1
    while os.path.exists(candidate):
        index += 1
        candidate = os.path.join(parent, f"{stem}-extracted-{index}")
    return candidate


def run_info(run_path: str) -> str:
    """Ejecuta `sh file.run --info`. Seguro: el stub solo imprime metadatos."""
    p = subprocess.run(
        ["sh", run_path, "--info"], capture_output=True, text=True, timeout=60
    )
    return (p.stdout or "") + (p.stderr or "")


def parse_info(text: str) -> dict:
    """Extrae campos clave del --info (compatible Makeself 2.2.x - 2.7.x)."""
    out: dict = {}
    patterns = {
        "identification": r"Identification:\s*(.+)",
        "target": r"Target directory:\s*(.+)",
        "uncompressed": r"Uncompressed size:\s*(.+)",
        "compression": r"Compression:\s*(.+)",
        "date": r"Date of packaging:\s*(.+)",
        "version": r"Built with Makeself version\s*(.+)",
        "script": r"Script run after extraction:\s*\n?\s*(.+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[key] = m.group(1).strip()
    return out


def extract_noexec(run_path: str, dest: str) -> subprocess.CompletedProcess:
    """Extrae a dest sin ejecutar startup_script. Seguro para inspeccionar."""
    return subprocess.run(
        ["sh", run_path, "--target", dest, "--noexec", "--keep"],
        capture_output=True,
        text=True,
        timeout=600,
    )


def run_check(run_path: str) -> subprocess.CompletedProcess:
    """Verifica CRC/MD5. Puede tardar en archivos grandes."""
    return subprocess.run(
        ["sh", run_path, "--check"], capture_output=True, text=True, timeout=1200
    )
