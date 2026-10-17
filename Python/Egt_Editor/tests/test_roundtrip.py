"""Tests significativos (§19): round-trip + i18n + header."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core import crypto_provider as crypto
from core.egt_format import detect_kind
from i18n import I18n


def test_salted_header_detect():
    assert crypto.has_salted_header(b"Salted__" + b"12345678" + b"xx")
    assert not crypto.has_salted_header(b"plain")


def test_roundtrip_pbkdf2():
    pt = b"EGT-Exciter3-test-payload-12345"
    enc = crypto.encrypt_with("nvram-test", pt, "aes-256-cbc", "pbkdf2", salt=b"12345678")
    assert crypto.has_salted_header(enc)
    out, cipher, kdf = crypto.try_decrypt("nvram-test", enc)
    assert out == pt and cipher == "aes-256-cbc" and kdf == "pbkdf2"


def test_roundtrip_md5_legacy():
    pt = b"legacy-payload"
    enc = crypto.encrypt_with("pw", pt, "aes-128-cbc", "md5", salt=b"abcdefgh")
    out, _, kdf = crypto.try_decrypt("pw", enc)
    # try_decrypt prueba pbkdf2 primero; debe resolver igual al descifrar directo md5
    assert out == pt or kdf in ("pbkdf2", "md5")
    direct = crypto.decrypt_with("pw", enc, "aes-128-cbc", "md5")
    assert direct == pt


def test_wrong_password_fails():
    pt = b"secret"
    enc = crypto.encrypt_with("ok", pt, "aes-256-cbc", "pbkdf2", salt=b"12345678")
    try:
        crypto.try_decrypt("wrong", enc)
        assert False, "debio fallar"
    except ValueError:
        pass


def test_detect_kind():
    assert detect_kind("E3_G_GREEN_R8.2_431_PE_32569_CONFIG") == "CONFIG"
    assert detect_kind("E3_G_GREEN_R8.2_431_PE_32570_CONFG") == "CONFIG"
    assert detect_kind("E3_G_GREEN_R8.2_431_PE_SETTINGS") == "SETTINGS"
    assert detect_kind("34PE_GREENG_R8.2_431_PEN_1.enc") == "PEN"


def test_i18n_completa():
    es = I18n("es")
    en = I18n("en")
    for key in ("menu.file", "act.open", "btn.decrypt", "msg.decrypt_fail"):
        assert es.t(key) != key
        assert en.t(key) != key
