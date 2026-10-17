"""Exportacion JSON/CSV round-trip (compatibilidad)."""
from __future__ import annotations

import base64
import csv
import json
from pathlib import Path

from .egt_format import EgtFile
from .nvram_xml import NvramDocument


def export_json(eg: EgtFile, dest: Path) -> Path:
    payload = {
        "filename": eg.path.name,
        "kind": eg.kind,
        "cipher": eg.cipher,
        "kdf": eg.kdf,
        "analysis": eg.analyze(),
        "plaintext_b64": base64.b64encode(eg.plaintext).decode() if eg.plaintext else None,
        "plaintext_hex": eg.plaintext.hex() if eg.plaintext else None,
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def import_plaintext_hex(src: Path) -> bytes:
    data = json.loads(src.read_text(encoding="utf-8"))
    hx = data.get("plaintext_hex")
    if not hx:
        raise ValueError("json-sin-plaintext")
    return bytes.fromhex(hx)


def export_nvram_json(doc: NvramDocument, dest: Path) -> Path:
    dest.write_text(json.dumps(doc.to_jsonable(), indent=1, ensure_ascii=False), encoding="utf-8")
    return dest


def export_nvram_csv(doc: NvramDocument, dest: Path) -> Path:
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "address", "size", "value", "section", "context"])
        for p in doc.parameters:
            w.writerow([p.name, p.address, p.size, p.value, p.section, p.context])
    return dest
