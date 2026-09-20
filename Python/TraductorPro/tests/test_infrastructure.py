import os
import tempfile

from traductor_pro.domain.entities import FileType
from traductor_pro.infrastructure.cache.md5_cache import Md5Cache
from traductor_pro.infrastructure.file_handlers.cfg_handler import CfgFileHandler
from traductor_pro.infrastructure.file_handlers.json_handler import JsonFileHandler
from traductor_pro.infrastructure.file_handlers.lang_handler import LangFileHandler
from traductor_pro.infrastructure.file_handlers.properties_handler import PropertiesFileHandler
from traductor_pro.infrastructure.file_handlers.txt_handler import TxtFileHandler
from traductor_pro.infrastructure.placeholder.placeholder_protector import RegexPlaceholderProtector
from traductor_pro.infrastructure.reports.text_report import TextReportGenerator
from traductor_pro.infrastructure.security.key_manager import KeyringKeyManager


class TestCfgFileHandler:
    def test_supported_type(self):
        handler = CfgFileHandler()
        assert handler.supported_type() == FileType.CFG

    def test_detect_type(self):
        handler = CfgFileHandler()
        assert handler.detect_type("test.cfg") is True
        assert handler.detect_type("test.txt") is False

    def test_read(self, sample_cfg_file):
        handler = CfgFileHandler()
        lines = handler.read(sample_cfg_file)
        assert len(lines) == 3
        assert lines[0].is_translatable is True
        assert lines[0].key == "key1"
        assert lines[0].value == "Hello World"
        assert lines[1].is_translatable is False

    def test_write(self, sample_cfg_file, tmp_dir):
        handler = CfgFileHandler()
        lines = handler.read(sample_cfg_file)
        lines[0].value = "Hola Mundo"
        output = os.path.join(tmp_dir, "out.cfg")
        handler.write(output, lines)

        result = handler.read(output)
        assert result[0].value == "Hola Mundo"
        assert result[1].raw_content == "# comment"


class TestLangFileHandler:
    def test_supported_type(self):
        handler = LangFileHandler()
        assert handler.supported_type() == FileType.LANG

    def test_detect_type(self):
        handler = LangFileHandler()
        assert handler.detect_type("test.lang") is True
        assert handler.detect_type("test.cfg") is False

    def test_read_with_placeholders(self, sample_lang_file):
        handler = LangFileHandler()
        lines = handler.read(sample_lang_file)
        assert len(lines) == 3
        assert lines[0].is_translatable is True
        assert "<player>" in lines[0].placeholders
        assert lines[1].is_translatable is True
        assert "%s" in lines[1].placeholders

    def test_read_protects_backslash_escapes(self, tmp_dir):
        import os
        path = os.path.join(tmp_dir, "esc.lang")
        with open(path, "w", encoding="utf-8") as f:
            f.write("k=Used.\\n\\nTier 1\\n")
        handler = LangFileHandler()
        lines = handler.read(path)
        assert lines[0].placeholders == ["\\n", "\\n", "\\n"]

    def test_write_preserves_crlf(self, tmp_dir):
        import os
        path = os.path.join(tmp_dir, "crlf.lang")
        with open(path, "wb") as f:
            f.write(b"k=Hello\r\n# c\r\n")
        handler = LangFileHandler()
        lines = handler.read(path)
        out = os.path.join(tmp_dir, "out.lang")
        handler.write(out, lines)
        with open(out, "rb") as f:
            content = f.read()
        assert b"\r\n" in content
        assert content.count(b"\r\n") == 2


class TestTxtFileHandler:
    def test_supported_type(self):
        handler = TxtFileHandler()
        assert handler.supported_type() == FileType.TXT

    def test_detect_type(self):
        handler = TxtFileHandler()
        assert handler.detect_type("test.txt") is True
        assert handler.detect_type("test.cfg") is False

    def test_read(self, sample_txt_file):
        handler = TxtFileHandler()
        lines = handler.read(sample_txt_file)
        assert len(lines) == 3
        assert lines[0].is_translatable is True
        assert lines[1].is_translatable is False
        assert lines[2].is_translatable is True


class TestPropertiesFileHandler:
    def test_supported_type(self):
        handler = PropertiesFileHandler()
        assert handler.supported_type() == FileType.PROPERTIES

    def test_detect_type(self):
        handler = PropertiesFileHandler()
        assert handler.detect_type("test.properties") is True
        assert handler.detect_type("test.cfg") is False

    def test_read(self, sample_properties_file):
        handler = PropertiesFileHandler()
        lines = handler.read(sample_properties_file)
        assert len(lines) == 4
        assert lines[0].is_translatable is False
        assert lines[1].is_translatable is True
        assert lines[1].key == "greeting"
        assert "{0}" in lines[1].placeholders
        assert lines[2].key == "farewell"
        assert "%s" in lines[2].placeholders
        assert lines[3].is_translatable is False

    def test_roundtrip(self, sample_properties_file, tmp_path):
        handler = PropertiesFileHandler()
        lines = handler.read(sample_properties_file)
        out = str(tmp_path / "out.properties")
        handler.write(out, lines)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "greeting=Hello {0}" in content
        assert "# comment" in content


class TestJsonFileHandler:
    def test_supported_type(self):
        handler = JsonFileHandler()
        assert handler.supported_type() == FileType.JSON

    def test_detect_type(self):
        handler = JsonFileHandler()
        assert handler.detect_type("test.json") is True
        assert handler.detect_type("test.txt") is False

    def test_read(self, sample_json_file):
        handler = JsonFileHandler()
        lines = handler.read(sample_json_file)
        by_key = {line.key: line for line in lines}
        assert by_key['["menu", "file"]'].is_translatable is True
        assert "{0}" in by_key['["menu", "file"]'].placeholders
        assert by_key['["count"]'].is_translatable is False
        assert by_key['["active"]'].is_translatable is False
        assert by_key['["nothing"]'].is_translatable is False
        assert by_key['["empty"]'].is_translatable is False

    def test_roundtrip_types(self, sample_json_file, tmp_path):
        import json
        handler = JsonFileHandler()
        lines = handler.read(sample_json_file)
        out = str(tmp_path / "out.json")
        handler.write(out, lines)
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        assert data["menu"]["file"] == "Open {0}"
        assert data["count"] == 3 and isinstance(data["count"], int)
        assert data["active"] is True
        assert data["nothing"] is None
        assert data["items"] == ["First %s", ""]
        assert data["empty"] == ""


class TestMd5Cache:
    def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Md5Cache(cache_dir=d)
            cache.set("test_key", "test_value")
            assert cache.get("test_key") == "test_value"

    def test_exists(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Md5Cache(cache_dir=d)
            assert cache.exists("nonexistent") is False
            cache.set("key1", "val1")
            assert cache.exists("key1") is True

    def test_clear(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Md5Cache(cache_dir=d)
            cache.set("k1", "v1")
            cache.set("k2", "v2")
            cache.clear()
            assert cache.get("k1") is None
            assert cache.get("k2") is None


class TestRegexPlaceholderProtector:
    def test_protect_xml_tags(self):
        protector = RegexPlaceholderProtector()
        result = protector.protect("Hello <player>")
        assert "<player>" not in result
        assert "⟦0⟧" in result

    def test_restore_xml_tags(self):
        protector = RegexPlaceholderProtector()
        protected = protector.protect("Hello <player>")
        restored = protector.restore(protected)
        assert restored == "Hello <player>"

    def test_percent_placeholders(self):
        protector = RegexPlaceholderProtector()
        protected = protector.protect("You have %s items and %d coins")
        restored = protector.restore(protected)
        assert restored == "You have %s items and %d coins"

    def test_curly_braces(self):
        protector = RegexPlaceholderProtector()
        protected = protector.protect("Value: {name}")
        restored = protector.restore(protected)
        assert restored == "Value: {name}"

    def test_mixed_placeholders(self):
        protector = RegexPlaceholderProtector()
        text = "Hello <b>{name}</b>, you have %s items"
        protected = protector.protect(text)
        restored = protector.restore(protected)
        assert restored == text


class TestTextReportGenerator:
    def test_generate(self):
        from traductor_pro.domain.entities import GlobalReport, TranslationReport, TranslationEngine
        report = GlobalReport(
            reports=[
                TranslationReport(
                    input_path="a.cfg",
                    output_path="out/a_es.cfg",
                    engine=TranslationEngine.GOOGLE,
                    target_lang="es",
                    attempted=5,
                    succeeded=4,
                    failed=1,
                )
            ],
            timestamp="2026-01-01T00:00:00",
        )
        gen = TextReportGenerator()
        text = gen.generate(report)
        assert "REPORTE DE TRADUCCIÓN" in text
        assert "a.cfg" in text
        assert "4" in text

    def test_save(self):
        from traductor_pro.domain.entities import GlobalReport, TranslationReport, TranslationEngine
        report = GlobalReport(
            reports=[
                TranslationReport(
                    input_path="a.cfg",
                    output_path="out/a_es.cfg",
                    engine=TranslationEngine.GOOGLE,
                    target_lang="es",
                )
            ],
            timestamp="2026-01-01T00:00:00",
        )
        gen = TextReportGenerator()
        with tempfile.TemporaryDirectory() as d:
            gen.save(report, d)
            assert os.path.isfile(os.path.join(d, "latest_report.txt"))
