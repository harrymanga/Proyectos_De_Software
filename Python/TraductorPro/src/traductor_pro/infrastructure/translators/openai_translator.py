import logging

from traductor_pro.domain.entities import TranslationRequest, TranslationResult
from traductor_pro.domain.interfaces import KeyManagerPort, TranslatorPort

logger = logging.getLogger(__name__)


class OpenAITranslatorAdapter(TranslatorPort):
    MODEL = "gpt-4o-mini"

    def __init__(self, key_manager: KeyManagerPort) -> None:
        self._key_manager = key_manager
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        api_key = self._key_manager.get_key("openai")
        if not api_key:
            raise RuntimeError("API key de OpenAI no configurada. Use Configuración > API Keys.")
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        except ImportError:
            raise RuntimeError("openai no está instalado. Ejecute: pip install openai")

    def translate(self, request: TranslationRequest) -> TranslationResult:
        try:
            self._ensure_client()
            source_lang = request.source_lang or "auto-detect"
            system_prompt = (
                f"You are a professional translator. "
                f"Translate the following text to {request.target_lang}. "
                f"Source language: {source_lang}. "
                f"Preserve all placeholders like <tag>, %s, %d, {{var}} exactly as they are. "
                f"Return ONLY the translated text, nothing else."
            )
            response = self._client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.source_text},
                ],
                temperature=0.3,
            )
            translated = response.choices[0].message.content.strip() if response.choices else ""
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
            logger.error("Error en OpenAI: %s", e)
            return TranslationResult(
                translated_text=request.source_text,
                success=False,
                error=str(e),
            )
