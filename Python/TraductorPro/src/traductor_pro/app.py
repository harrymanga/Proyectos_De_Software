#!/usr/bin/env python3
import logging
import sys

from PyQt5.QtWidgets import QApplication

from traductor_pro.application.use_cases import (
    ManageApiKeysUseCase,
    TranslateBatchUseCase,
    TranslateFileUseCase,
)
from traductor_pro.infrastructure.cache.md5_cache import Md5Cache
from traductor_pro.infrastructure.file_handlers.cfg_handler import CfgFileHandler
from traductor_pro.infrastructure.file_handlers.json_handler import JsonFileHandler
from traductor_pro.infrastructure.file_handlers.lang_handler import LangFileHandler
from traductor_pro.infrastructure.file_handlers.properties_handler import PropertiesFileHandler
from traductor_pro.infrastructure.file_handlers.txt_handler import TxtFileHandler
from traductor_pro.infrastructure.placeholder.placeholder_protector import RegexPlaceholderProtector
from traductor_pro.infrastructure.reports.text_report import TextReportGenerator
from traductor_pro.infrastructure.security.key_manager import KeyringKeyManager
from traductor_pro.infrastructure.translators.translator_factory import TranslatorFactory
from traductor_pro.presentation.main_window import MainWindowController


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> int:
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("TraductorPro")
    app.setOrganizationName("TraductorPro")

    key_manager = KeyringKeyManager()
    cache = Md5Cache()
    protector = RegexPlaceholderProtector()
    report_gen = TextReportGenerator()

    translators = TranslatorFactory.create_all(key_manager)
    file_handlers = {
        handler.supported_type(): handler
        for handler in [CfgFileHandler(), LangFileHandler(), TxtFileHandler(),
                          PropertiesFileHandler(), JsonFileHandler()]
    }

    translate_file_uc = TranslateFileUseCase(
        translators=translators,
        file_handlers=file_handlers,
        cache=cache,
        placeholder_protector=protector,
        report_generator=report_gen,
        key_manager=key_manager,
    )

    batch_uc = TranslateBatchUseCase(translate_file_uc)
    keys_uc = ManageApiKeysUseCase(key_manager)

    window = MainWindowController(
        translate_file_use_case=translate_file_uc,
        batch_use_case=batch_uc,
        key_use_case=keys_uc,
        cache_port=cache,
        report_generator=report_gen,
    )
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
