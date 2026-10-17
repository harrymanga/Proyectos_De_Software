"""Modelo EGT Exciter 3. Fase esqueleto: conserva bytes, edicion a nivel plaintext."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def detect_kind(filename: str) -> str:
    u = filename.upper()
    if u.endswith(".XML"):
        return "NVRAM_XML"
    if "PEN" in u or "USD" in u or "SOL" in u:
        return "PEN"
    if "SETTINGS" in u:
        return "SETTINGS"
    if "CONFIG" in u or "CONFG" in u:
        return "CONFIG"
    if u.startswith("FROM"):
        return "CONVERT"
    if "~" in filename:
        return "NVRAM_DATA"
    if u.endswith(".BIN"):
        return "SS_BIN"
    return "UNKNOWN"


def detect_content_kind(data: bytes) -> str:
    """Clasificacion por contenido (§4: no fiarse del nombre)."""
    if data[:5] == b"<?xml":
        return "NVRAM_XML"
    if len(data) >= 8 and data[:8] == b"Salted__":
        return "CRYPT_SALTED"
    return "BLOB"


@dataclass
class EgtFile:
    path: Path
    kind: str
    encrypted: bytes
    plaintext: bytes | None = None
    cipher: str = ""
    kdf: str = ""
    fields: dict = field(default_factory=dict)

    @property
    def decrypted(self) -> bool:
        return self.plaintext is not None

    def analyze(self) -> dict:
        """Heuristica minima: texto vs binario + tamano. Se ampliara en Fase 2."""
        if self.plaintext is None:
            return {"state": "encrypted", "size_enc": len(self.encrypted)}
        pt = self.plaintext
        text_chars = sum(32 <= b < 127 or b in (9, 10, 13) for b in pt)
        ratio = text_chars / max(1, len(pt))
        return {
            "state": "decrypted",
            "size_enc": len(self.encrypted),
            "size_plain": len(pt),
            "text_ratio": round(ratio, 3),
            "looks_text": ratio > 0.85,
        }

    def set_plaintext_from_hex(self, hex_text: str) -> None:
        clean = "".join(hex_text.split())
        self.plaintext = bytes.fromhex(clean)
