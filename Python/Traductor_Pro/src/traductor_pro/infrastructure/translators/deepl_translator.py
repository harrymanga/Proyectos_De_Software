import logging
from typing import Optional

from traductor_pro.domain.entities import TranslationRequest, TranslationResult
from traductor_pro.domain.interfaces import KeyManagerPort, TranslatorPort

logger = logging.getLogger(__name__)


class DeepLTranslatorAdapter(TranslatorPort):
    def __init__(self, key_manager: KeyManagerPort) -> None:
        self._key_manager = key_manager
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        api_key = self._key_manager.get_key("deepl")
        if not api_key:
            raise RuntimeError("API key de DeepL no configurada. Use Configuración > API Keys.")
        try:
            import deepl
            self._client = deepl.Translator(api_key)
        except ImportError:
            raise RuntimeError("deepl no está instalado. Ejecute: pip install deepl")

    def translate(self, request: TranslationRequest) -> TranslationResult:
        try:
            self._ensure_client()
            kwargs: dict = {"target_lang": request.target_lang.upper()}
            if request.source_lang:
                kwargs["source_lang"] = request.source_lang.upper()
            result = self._client.translate_text(request.source_text, **kwargs)
            translated = result.text if result else ""
            if not translated:
                return TranslationResult(
                    translated_text=request.source_text,
                    success=False,
                    error="Traducción vacía",
                )
            return TranslationResult(translated_text=translated, success=True)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Error en DeepL: %s", e)
            return TranslationResult(
                translated_text=request.source_text,
                success=False,
                error=str(e),
            )
