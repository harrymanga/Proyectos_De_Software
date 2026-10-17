"""Tests NVRAM-XML con archivos reales (§19: comportamiento significativo)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.nvram_xml import parse_nvram_xml, serialize
from core.egt_format import detect_content_kind, detect_kind
from core.exporter import export_nvram_csv, export_nvram_json
from i18n import I18n

XML_REF = Path("/home/handerson/Descargas/Test/EGT/E3_C_GOLD-HD_R7_408_P92~GOLD OFICINA")


def test_parse_real_xml():
    doc = parse_nvram_xml(XML_REF)
    assert len(doc.parameters) == 4762
    assert doc.game_version == "E3_C_GOLD-HD_R7_408_P92"
    assert doc.crc == "1901404099899257991"
    assert doc.validate() == []
    p = doc.get("NVRAM_BILL_VALIDATOR")
    assert p is not None and p.address == "974"


def test_edit_and_reserialize_roundtrip(tmp_path):
    doc = parse_nvram_xml(XML_REF)
    assert doc.set_value("NVRAM_BILL_VALIDATOR", "5")
    assert doc.get("NVRAM_BILL_VALIDATOR").value == "5"
    out = serialize(doc)
    assert 'name="NVRAM_BILL_VALIDATOR"' in out and 'value="5"' in out
    assert f'CRC="{doc.crc}"' in out  # CRC preservado
    dest = tmp_path / "reser.xml"
    dest.write_text(out, encoding="utf-8")
    doc2 = parse_nvram_xml(dest)
    assert len(doc2.parameters) == 4762
    assert doc2.get("NVRAM_BILL_VALIDATOR").value == "5"


def test_validate_detecta_size_mismatch():
    doc = parse_nvram_xml(XML_REF)
    p = doc.parameters[0]  # NVRAM_BILL_CHANNELS size=400
    doc.set_value(p.name, "1 2 3")
    errors = doc.validate()
    assert any(p.name in e for e in errors)


def test_detect_content_kind():
    assert detect_content_kind(b"<?xml version") == "NVRAM_XML"
    assert detect_content_kind(b"Salted__12345678xx") == "CRYPT_SALTED"
    assert detect_content_kind(b"\x00\x41\x4d\xa9") == "BLOB"


def test_detect_kind_names():
    assert detect_kind("E3_G_GREEN_R8.2_431_PE_32569_CONFIG") == "CONFIG"
    assert detect_kind("FROM1_TO34_1.enc") == "CONVERT"
    assert detect_kind("E3_C_RED_R6.2_362_P92_PE_34995_CONFG") == "CONFIG"
    assert detect_kind("SS_BL5A_135_000_1_1_a.ppjs.bin") == "SS_BIN"


def test_export_json_csv(tmp_path):
    doc = parse_nvram_xml(XML_REF)
    j = export_nvram_json(doc, tmp_path / "p.json")
    c = export_nvram_csv(doc, tmp_path / "p.csv")
    assert j.stat().st_size > 100000
    lines = c.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4763  # header + params


def test_i18n_nuevas_claves():
    for code in ("es", "en"):
        t = I18n(code)
        for key in ("tab.nvram", "act.save_xml", "act.export_csv", "msg.xml_saved", "lbl.filter"):
            assert t.t(key) != key, (code, key)
