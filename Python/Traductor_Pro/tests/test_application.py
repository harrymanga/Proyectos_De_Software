import os

from traductor_pro.application.use_cases import (
    ManageApiKeysUseCase,
    TranslateBatchUseCase,
    TranslateFileUseCase,
    TranslateTextUseCase,
)
from traductor_pro.domain.entities import (
    FileTranslationJob,
    FileType,
    TranslationEngine,
    TranslationRequest,
)
from traductor_pro.infrastructure.cache.md5_cache import Md5Cache
from traductor_pro.infrastructure.file_handlers.cfg_handler import CfgFileHandler
from traductor_pro.infrastructure.file_handlers.lang_handler import LangFileHandler
from traductor_pro.infrastructure.file_handlers.txt_handler import TxtFileHandler
from traductor_pro.infrastructure.placeholder.placeholder_protector import RegexPlaceholderProtector
from traductor_pro.infrastructure.reports.text_report import TextReportGenerator


class TestTranslateTextUseCase:
    def test_basic_translation(self, fake_translator, fake_cache, fake_protector):
        uc = TranslateTextUseCase(fake_translator, fake_cache, fake_protector)
        request = TranslationRequest(
            source_text="Hello",
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
        )
        result = uc.execute(request)
        assert result.success is True
        assert result.translated_text == "TR_Hello"
        assert result.from_cache is False

    def test_cache_hit(self, fake_translator, fake_cache, fake_protector):
        uc = TranslateTextUseCase(fake_translator, fake_cache, fake_protector)
        request = TranslationRequest(
            source_text="Hello",
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
        )
        result1 = uc.execute(request)
        assert result1.from_cache is False

        result2 = uc.execute(request)
        assert result2.from_cache is True
        assert result2.translated_text == result1.translated_text
        assert fake_translator.call_count == 1

    def test_empty_text(self, fake_translator, fake_cache, fake_protector):
        uc = TranslateTextUseCase(fake_translator, fake_cache, fake_protector)
        request = TranslationRequest(
            source_text="",
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
        )
        result = uc.execute(request)
        assert result.success is True
        assert result.translated_text == ""

    def test_placeholder_protection(self, fake_translator, fake_cache):
        protector = RegexPlaceholderProtector()
        uc = TranslateTextUseCase(fake_translator, fake_cache, protector)
        request = TranslationRequest(
            source_text="Hello <player>, you have %s items",
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
        )
        result = uc.execute(request)
        assert result.success is True
        assert "<player>" in result.translated_text
        assert "%s" in result.translated_text


class TestTranslateFileUseCase:
    def _make_uc(self, fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager):
        handlers = {
            FileType.CFG: CfgFileHandler(),
            FileType.LANG: LangFileHandler(),
            FileType.TXT: TxtFileHandler(),
        }
        translators = {
            TranslationEngine.GOOGLE: fake_translator,
        }
        return TranslateFileUseCase(
            translators=translators,
            file_handlers=handlers,
            cache=fake_cache,
            placeholder_protector=fake_protector,
            report_generator=fake_report_gen,
            key_manager=fake_key_manager,
        )

    def test_translate_cfg(self, fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager, sample_cfg_file, tmp_dir):
        uc = self._make_uc(fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager)
        output = os.path.join(tmp_dir, "output.cfg")
        job = FileTranslationJob(
            input_path=sample_cfg_file,
            output_path=output,
            file_type=FileType.CFG,
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
            backup_original=False,
        )
        report = uc.execute(job)
        assert report.succeeded == 2
        assert report.failed == 0
        assert os.path.isfile(output)

        with open(output, "r", encoding="utf-8") as f:
            content = f.read()
        assert "TR_Hello World" in content
        assert "# comment" in content

    def test_translate_lang(self, fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager, sample_lang_file, tmp_dir):
        uc = self._make_uc(fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager)
        output = os.path.join(tmp_dir, "output.lang")
        job = FileTranslationJob(
            input_path=sample_lang_file,
            output_path=output,
            file_type=FileType.LANG,
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
            backup_original=False,
        )
        report = uc.execute(job)
        assert report.succeeded == 3
        assert os.path.isfile(output)

    def test_translate_txt(self, fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager, sample_txt_file, tmp_dir):
        uc = self._make_uc(fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager)
        output = os.path.join(tmp_dir, "output.txt")
        job = FileTranslationJob(
            input_path=sample_txt_file,
            output_path=output,
            file_type=FileType.TXT,
            target_lang="es",
            engine=TranslationEngine.GOOGLE,
            backup_original=False,
        )
        report = uc.execute(job)
        assert report.succeeded == 2
        assert os.path.isfile(output)


class TestTranslateBatchUseCase:
    def test_batch(self, fake_translator, fake_cache, fake_protector, fake_report_gen, fake_key_manager, sample_cfg_file, sample_txt_file, tmp_dir):
        handlers = {
            FileType.CFG: CfgFileHandler(),
            FileType.TXT: TxtFileHandler(),
        }
        translators = {TranslationEngine.GOOGLE: fake_translator}
        file_uc = TranslateFileUseCase(
            translators=translators,
            file_handlers=handlers,
            cache=fake_cache,
            placeholder_protector=fake_protector,
            report_generator=fake_report_gen,
            key_manager=fake_key_manager,
        )
        batch_uc = TranslateBatchUseCase(file_uc)

        jobs = [
            FileTranslationJob(
                input_path=sample_cfg_file,
                output_path=os.path.join(tmp_dir, "out1.cfg"),
                file_type=FileType.CFG,
                target_lang="es",
                engine=TranslationEngine.GOOGLE,
                backup_original=False,
            ),
            FileTranslationJob(
                input_path=sample_txt_file,
                output_path=os.path.join(tmp_dir, "out2.txt"),
                file_type=FileType.TXT,
                target_lang="es",
                engine=TranslationEngine.GOOGLE,
                backup_original=False,
            ),
        ]
        report = batch_uc.execute(jobs)
        assert report.total_files == 2
        assert report.total_succeeded > 0


class TestManageApiKeysUseCase:
    def test_set_and_get(self, fake_key_manager):
        uc = ManageApiKeysUseCase(fake_key_manager)
        uc.set("deepl", "test-key-123")
        assert uc.get("deepl") == "test-key-123"

    def test_delete(self, fake_key_manager):
        uc = ManageApiKeysUseCase(fake_key_manager)
        uc.set("openai", "key-456")
        uc.delete("openai")
        assert uc.get("openai") is None
