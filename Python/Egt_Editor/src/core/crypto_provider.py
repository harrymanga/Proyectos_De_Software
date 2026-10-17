"""Interop openssl Salted__ (§25: sin secretos en logs)."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

SALT_MAGIC = b"Salted__"
HEADER_LEN = 16

# Candidatos ordenados: primero pbkdf2 moderno, luego md5 legacy.
CANDIDATES = [
    ("aes-256-cbc", "pbkdf2"),
    ("aes-128-cbc", "pbkdf2"),
    ("aes-256-cbc", "md5"),
    ("aes-128-cbc", "md5"),
]


def has_salted_header(data: bytes) -> bool:
    return len(data) >= HEADER_LEN and data[:8] == SALT_MAGIC


def split_header(data: bytes) -> tuple[bytes, bytes]:
    if not has_salted_header(data):
        raise ValueError("not-salted-header")
    return data[8:16], data[16:]


def _evp_bytes_to_key(password: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    # Derivacion legacy openssl enc -md md5 (sin pbkdf2).
    out = b""
    prev = b""
    while len(out) < key_len + iv_len:
        prev = hashlib.md5(prev + password + salt).digest()
        out += prev
    return out[:key_len], out[key_len:key_len + iv_len]


def _pbkdf2_key(password: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    # openssl enc -pbkdf2 por defecto: sha256, 10000 iteraciones.
    material = hashlib.pbkdf2_hmac("sha256", password, salt, 10000, key_len + iv_len)
    return material[:key_len], material[key_len:]


def _cipher_key_len(cipher: str) -> int:
    if cipher.startswith("aes-256"):
        return 32
    if cipher.startswith("aes-128"):
        return 16
    raise ValueError(f"unsupported-cipher:{cipher}")


def decrypt_with(password: str, data: bytes, cipher: str, kdf: str) -> bytes:
    """DescifraAES-CBC con padding PKCS7. Lanza ValueError si falla."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    salt, ct = split_header(data)
    key_len = _cipher_key_len(cipher)
    pw = password.encode("utf-8")
    if kdf == "pbkdf2":
        key, iv = _pbkdf2_key(pw, salt, key_len, 16)
    elif kdf == "md5":
        key, iv = _evp_bytes_to_key(pw, salt, key_len, 16)
    else:
        raise ValueError(f"unsupported-kdf:{kdf}")
    if cipher.endswith("ecb"):
        raise ValueError("ecb-no-saltable")
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = dec.update(ct) + dec.finalize()
    pad = padded[-1]
    if pad < 1 or pad > 16 or len(padded) < pad:
        raise ValueError("bad-decrypt")
    if padded[-pad:] != bytes([pad]) * pad:
        raise ValueError("bad-decrypt")
    return padded[:-pad]


def try_decrypt(password: str, data: bytes) -> tuple[bytes, str, str]:
    """Prueba candidatos en orden. Retorna (plaintext, cipher, kdf)."""
    errors: list[str] = []
    for cipher, kdf in CANDIDATES:
        try:
            return decrypt_with(password, data, cipher, kdf), cipher, kdf
        except Exception as e:  # noqa: BLE001 - se agrega contexto sin secretos
            errors.append(f"{cipher}/{kdf}:{e}")
    raise ValueError("bad-decrypt|candidates=" + ";".join(errors))


def encrypt_with(password: str, plaintext: bytes, cipher: str, kdf: str, salt: bytes | None = None) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    key_len = _cipher_key_len(cipher)
    salt = salt or os.urandom(8)
    pw = password.encode("utf-8")
    if kdf == "pbkdf2":
        key, iv = _pbkdf2_key(pw, salt, key_len, 16)
    else:
        key, iv = _evp_bytes_to_key(pw, salt, key_len, 16)
    pad = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad]) * pad
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return SALT_MAGIC + salt + enc.update(padded) + enc.finalize()


@dataclass
class Session:
    cipher: str = CANDIDATES[0][0]
    kdf: str = CANDIDATES[0][1]
    salt: bytes | None = None
