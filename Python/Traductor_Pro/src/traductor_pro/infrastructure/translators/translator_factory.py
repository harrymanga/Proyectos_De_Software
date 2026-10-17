from typing import Dict

from traductor_pro.domain.entities import TranslationEngine
from traductor_pro.domain.interfaces import KeyManagerPort, TranslatorPort
from traductor_pro.infrastructure.translators.deepl_translator import DeepLTranslatorAdapter
from traductor_pro.infrastructure.translators.google_translator import GoogleTranslatorAdapter
from traductor_pro.infrastructure.translators.openai_translator import OpenAITranslatorAdapter
from traductor_pro.infrastructure.translators.transshell_translator import TransShellTranslatorAdapter


class TranslatorFactory:
    @staticmethod
    def create_all(key_manager: KeyManagerPort) -> Dict[TranslationEngine, TranslatorPort]:
        return {
            TranslationEngine.GOOGLE: GoogleTranslatorAdapter(),
            TranslationEngine.DEEPL: DeepLTranslatorAdapter(key_manager),
            TranslationEngine.OPENAI: OpenAITranslatorAdapter(key_manager),
            TranslationEngine.TRANSSHELL: TransShellTranslatorAdapter(),
        }

    @staticmethod
    def create(engine: TranslationEngine, key_manager: KeyManagerPort) -> TranslatorPort:
        factories = {
            TranslationEngine.GOOGLE: lambda: GoogleTranslatorAdapter(),
            TranslationEngine.DEEPL: lambda: DeepLTranslatorAdapter(key_manager),
            TranslationEngine.OPENAI: lambda: OpenAITranslatorAdapter(key_manager),
            TranslationEngine.TRANSSHELL: lambda: TransShellTranslatorAdapter(),
        }
        factory = factories.get(engine)
        if factory is None:
            raise ValueError(f"Motor de traducción no soportado: {engine}")
        return factory()
