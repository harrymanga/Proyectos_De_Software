import os
import tempfile

from traductor_pro.application.use_cases import (
    ManageApiKeysUseCase,
    TranslateBatchUseCase,
    TranslateFileUseCase,
)
from traductor_pro.domain.entities import (
    FileTranslationJob,
    FileType,
    TranslationEngine,
)
from traductor_pro.infrastructure.cache.md5_cache import Md5Cache
from traductor_pro.infrastructure.file_handlers.cfg_handler import CfgFileHandler
from traductor_pro.infrastructure.file_handlers.lang_handler import LangFileHandler
from traductor_pro.infrastructure.file_handlers.txt_handler import TxtFileHandler
from traductor_pro.infrastructure.placeholder.placeholder_protector import RegexPlaceholderProtector
from traductor_pro.infrastructure.reports.text_report import TextReportGenerator
from traductor_pro.infrastructure.security.key_manager import KeyringKeyManager

from tests.conftest import FakeTranslator, FakeCache, FakeKeyManager, FakePlaceholderProtector, FakeReportGenerator


class TestIntegrationCfg:
    def test_full_pipeline_cfg(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Md5Cache(cache_dir=os.path.join(tmp, "cache"))
            protector = RegexPlaceholderProtector()
            report_gen = TextReportGenerator()
            key_mgr = FakeKeyManager()
            translator = FakeTranslator(prefix="ES_")

            handlers = {FileType.CFG: CfgFileHandler()}
            translators = {TranslationEngine.GOOGLE: translator}

            uc = TranslateFileUseCase(
                translators=translators,
                file_handlers=handlers,
                cache=cache,
                placeholder_protector=protector,
                report_generator=report_gen,
                key_manager=key_mgr,
            )

            input_path = os.path.join(tmp, "input.cfg")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("greeting=Hello\n")
                f.write("farewell=Goodbye\n")
                f.write("# comment line\n")

            output_path = os.path.join(tmp, "output_es.cfg")
            job = FileTranslationJob(
                input_path=input_path,
                output_path=output_path,
                file_type=FileType.CFG,
                target_lang="es",
                engine=TranslationEngine.GOOGLE,
                backup_original=False,
            )

            report = uc.execute(job)
            assert report.succeeded == 2
            assert report.failed == 0

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "greeting=ES_Hello" in content
            assert "farewell=ES_Goodbye" in content
            assert "# comment line" in content


class TestIntegrationLang:
    def test_full_pipeline_lang_with_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Md5Cache(cache_dir=os.path.join(tmp, "cache"))
            protector = RegexPlaceholderProtector()
            report_gen = TextReportGenerator()
            key_mgr = FakeKeyManager()
            translator = FakeTranslator(prefix="TR_")

            handlers = {FileType.LANG: LangFileHandler()}
            translators = {TranslationEngine.GOOGLE: translator}

            uc = TranslateFileUseCase(
                translators=translators,
                file_handlers=handlers,
                cache=cache,
                placeholder_protector=protector,
                report_generator=report_gen,
                key_manager=key_mgr,
            )

            input_path = os.path.join(tmp, "input.lang")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("msg.welcome=Welcome <player>!\n")
                f.write("msg.items=You have %s items\n")

            output_path = os.path.join(tmp, "output_es.lang")
            job = FileTranslationJob(
                input_path=input_path,
                output_path=output_path,
                file_type=FileType.LANG,
                target_lang="es",
                engine=TranslationEngine.GOOGLE,
                backup_original=False,
            )

            report = uc.execute(job)
            assert report.succeeded == 2

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "<player>" in content
            assert "%s" in content


class TestIntegrationCustomReplacements:
    def test_replacements_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Md5Cache(cache_dir=os.path.join(tmp, "cache"))
            protector = RegexPlaceholderProtector()
            report_gen = TextReportGenerator()
            key_mgr = FakeKeyManager()
            translator = FakeTranslator(prefix="")

            handlers = {FileType.TXT: TxtFileHandler()}
            translators = {TranslationEngine.GOOGLE: translator}

            uc = TranslateFileUseCase(
                translators=translators,
                file_handlers=handlers,
                cache=cache,
                placeholder_protector=protector,
                report_generator=report_gen,
                key_manager=key_mgr,
            )

            input_path = os.path.join(tmp, "input.txt")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("Tin is a metal\n")

            output_path = os.path.join(tmp, "output_es.txt")
            job = FileTranslationJob(
                input_path=input_path,
                output_path=output_path,
                file_type=FileType.TXT,
                target_lang="es",
                engine=TranslationEngine.GOOGLE,
                custom_replacements={"Tin": "Estaño"},
                backup_original=False,
            )

            report = uc.execute(job)
            assert report.succeeded == 1

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "Estaño" in content
