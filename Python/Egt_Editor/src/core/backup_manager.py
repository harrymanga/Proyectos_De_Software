"""Backups reversibles (§41)."""
from pathlib import Path
import shutil
from datetime import datetime


def make_backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = path.with_suffix(path.suffix + f".{ts}.bak")
    shutil.copy2(path, bak)
    return bak
