import asyncio
import logging

from traductor_pro.domain.entities import TranslationRequest, TranslationResult
from traductor_pro.domain.interfaces import TranslatorPort

logger = logging.getLogger(__name__)


class GoogleTranslatorAdapter(TranslatorPort):
    def __init__(self) -> None:
        self._translator = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _ensure_translator(self) -> None:
        if self._translator is None:
            try:
                from googletrans import Translator
                self._translator = Translator()
            except ImportError:
                raise RuntimeError("googletrans no está instalado. Ejecute: pip install googletrans>=4.0.0-rc1")

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def translate(self, request: TranslationRequest) -> TranslationResult:
        try:
            self._ensure_translator()
            kwargs: dict = {"dest": request.target_lang, "src": request.source_lang or "auto"}
            loop = self._get_loop()
            result = loop.run_until_complete(self._translator.translate(request.source_text, **kwargs))
            translated = result.text if result else ""
            if not translated:
                return TranslationResult(
                    translated_text=request.source_text,
                    success=False,
                    error="Traducción vacía",
                )
            if translated.strip() == request.source_text.strip() and request.source_text.strip():
                # El endpoint a veces responde con eco (throttling): marcar
                # fallo visible en vez de cachear basura como válida.
                return TranslationResult(
                    translated_text=request.source_text,
                    success=False,
                    error="motor devolvió texto idéntico (posible límite)",
                )
            return TranslationResult(translated_text=translated, success=True)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Error en Google Translate: %s", e)
            return TranslationResult(
                translated_text=request.source_text,
                success=False,
                error=str(e),
            )
