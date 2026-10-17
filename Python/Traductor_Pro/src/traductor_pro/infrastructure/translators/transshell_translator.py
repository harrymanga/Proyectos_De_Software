import logging
import shutil
import subprocess

from traductor_pro.domain.entities import TranslationEngine, TranslationRequest, TranslationResult
from traductor_pro.domain.interfaces import TranslatorPort

logger = logging.getLogger(__name__)


def _is_echo(source: str, translated: str) -> bool:
    """Detecta eco del motor (devuelve la entrada, típico bajo throttling).

    Solo se considera eco si hay letras (evita falsos positivos con
    códigos como "Tier 1"... que aun así se marcan: visible > silencioso).
    En realidad se marca siempre que el texto sea idéntico: un "fallo
    visible" es preferible a basura cacheada como válida.
    """
    return bool(source.strip()) and translated.strip() == source.strip()


class TransShellTranslatorAdapter(TranslatorPort):
    """Motor gratuito vía CLI translate-shell (`trans`, endpoints alternos).

    Cubre al adaptador Google cuando su endpoint responde con eco
    (throttling). Requiere el paquete `translate-shell` del sistema.
    """

    def __init__(self, engine: str = "google") -> None:
        self._engine = engine

    def _ensure_binary(self) -> str:
        path = shutil.which("trans")
        if not path:
            raise RuntimeError(
                "translate-shell no está instalado. Ejecute: "
                "sudo apt install translate-shell"
            )
        return path

    def translate(self, request: TranslationRequest) -> TranslationResult:
        try:
            binary = self._ensure_binary()
            cmd = [binary, "-brief", f":{request.target_lang}", request.source_text]
            if self._engine != "google":
                cmd[1:1] = ["-e", self._engine]
            if request.source_lang:
                cmd[2] = f"{request.source_lang}:{request.target_lang}"
            completed = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
            translated = (completed.stdout or "").strip()
            if completed.returncode != 0 or not translated:
                return TranslationResult(
                    translated_text=request.source_text,
                    success=False,
                    error=(completed.stderr or "").strip() or "trans-shell sin salida",
                )
            if _is_echo(request.source_text, translated):
                return TranslationResult(
                    translated_text=request.source_text,
                    success=False,
                    error="motor devolvió texto idéntico (posible límite)",
                )
            return TranslationResult(translated_text=translated, success=True)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Error en trans-shell: %s", e)
            return TranslationResult(
                translated_text=request.source_text,
                success=False,
                error=str(e),
            )
