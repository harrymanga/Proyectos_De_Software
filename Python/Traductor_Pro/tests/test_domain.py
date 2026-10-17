from traductor_pro.domain.entities import (
    FileType,
    GlobalReport,
    ParsedLine,
    TranslationEngine,
    TranslationReport,
    TranslationRequest,
    TranslationResult,
)


class TestTranslationEngine:
    def test_values(self):
        assert TranslationEngine.GOOGLE.value == "google"
        assert TranslationEngine.DEEPL.value == "deepl"
        assert TranslationEngine.OPENAI.value == "openai"


class TestFileType:
    def test_values(self):
        assert FileType.CFG.value == "cfg"
        assert FileType.LANG.value == "lang"
        assert FileType.TXT.value == "txt"


class TestTranslationRequest:
    def test_creation(self):
        req = TranslationRequest(
            source_text="Hello",
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
        )
        assert req.source_text == "Hello"
        assert req.target_lang == "es"
        assert req.source_lang is None

    def test_with_source_lang(self):
        req = TranslationRequest(
            source_text="Hello",
            target_lang="es",
            engine=TranslationEngine.DEEPL,
            source_lang="en",
        )
        assert req.source_lang == "en"


class TestTranslationResult:
    def test_success(self):
        result = TranslationResult(translated_text="Hola", success=True)
        assert result.success is True
        assert result.from_cache is False
        assert result.error is None

    def test_failure(self):
        result = TranslationResult(
            translated_text="Hello",
            success=False,
            error="API error",
        )
        assert result.success is False
        assert result.error == "API error"


class TestParsedLine:
    def test_translatable(self):
        line = ParsedLine(
            line_number=1,
            raw_content="key=value",
            is_translatable=True,
            key="key",
            value="value",
        )
        assert line.is_translatable is True
        assert line.key == "key"
        assert line.value == "value"

    def test_non_translatable(self):
        line = ParsedLine(
            line_number=2,
            raw_content="# comment",
            is_translatable=False,
        )
        assert line.is_translatable is False


class TestGlobalReport:
    def test_empty_report(self):
        report = GlobalReport()
        assert report.total_files == 0
        assert report.total_attempted == 0

    def test_with_reports(self):
        r1 = TranslationReport(
            input_path="a.cfg",
            output_path="out/a_es.cfg",
            engine=TranslationEngine.GOOGLE,
            target_lang="es",
            attempted=5,
            succeeded=4,
            failed=1,
            cached=2,
        )
        r2 = TranslationReport(
            input_path="b.lang",
            output_path="out/b_es.lang",
            engine=TranslationEngine.DEEPL,
            target_lang="es",
            attempted=3,
            succeeded=3,
            failed=0,
            cached=1,
        )
        report = GlobalReport(reports=[r1, r2])
        assert report.total_files == 2
        assert report.total_attempted == 8
        assert report.total_succeeded == 7
        assert report.total_failed == 1
        assert report.total_cached == 3
