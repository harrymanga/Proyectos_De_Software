"""Internacionalización de Mod_Maker.

Norma §14 y §57: idiomas en archivos JSON separados con carga dinámica.
Español por defecto con fallback; cada clave existe en todos los idiomas.
Agregar un idioma es añadir un archivo, cero cambios de código.
"""

from __future__ import annotations

import json
from pathlib import Path

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

LANG_DIR = Path(__file__).resolve().parent.parent / "lang"
DEFAULT_LANGUAGE = "es"
FALLBACK_LANGUAGE = "en"


class I18nManager:
    """Carga traducciones desde archivos JSON y provee el método translate()."""

    def __init__(self, lang_dir: Path | None = None, language: str = DEFAULT_LANGUAGE) -> None:
        self.lang_dir = lang_dir or LANG_DIR
        self.language = language
        self._translations: dict[str, dict] = {}
        self._load_all()
        self._set_language(language)

    def _load_all(self) -> None:
        """Carga todos los archivos lang_xx.json disponibles."""
        if not self.lang_dir.exists():
            logger.warning("Directorio de idiomas no encontrado: %s", self.lang_dir)
            return
        for lang_file in sorted(self.lang_dir.glob("lang_*.json")):
            code = lang_file.stem[len("lang_") :]
            try:
                with lang_file.open("r", encoding="utf-8") as f:
                    self._translations[code] = json.load(f)
                logger.debug("Idioma cargado: %s (%s)", code, lang_file.name)
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("No se pudo cargar el idioma %s: %s", code, exc)

    def _set_language(self, language: str) -> None:
        if language not in self._translations:
            logger.warning(
                "Idioma '%s' no disponible, usando fallback '%s'", language, DEFAULT_LANGUAGE
            )
            language = DEFAULT_LANGUAGE
        if language not in self._translations:
            logger.error("No hay traducciones cargadas; el idioma por defecto tampoco existe")
            self.language = "en"
        else:
            self.language = language

    def set_language(self, language: str) -> None:
        """Cambia el idioma activo."""
        self._set_language(language)

    def get_available_languages(self) -> list[str]:
        """Devuelve la lista de códigos de idioma disponibles."""
        return sorted(self._translations.keys())

    def translate(self, key: str, **kwargs) -> str:
        """Traduce una clave al idioma activo con fallback a inglés y español."""
        text = self._lookup(key, self.language)
        if text is None:
            text = self._lookup(key, FALLBACK_LANGUAGE)
        if text is None:
            text = self._lookup(key, DEFAULT_LANGUAGE)
        if text is None:
            logger.warning("Clave de traducción faltante: %s", key)
            return key
        return text.format(**kwargs) if kwargs else text

    def _lookup(self, key: str, language: str) -> str | None:
        translations = self._translations.get(language, {})
        return translations.get(key)

    def validate_keys(self) -> list[str]:
        """Devuelve claves que faltan en algún idioma (huérfanas o incompletas)."""
        if not self._translations:
            return []
        reference = self._translations.get(DEFAULT_LANGUAGE, {})
        missing: list[str] = []
        for key in reference:
            for lang, translations in self._translations.items():
                if key not in translations:
                    missing.append(f"{lang}:{key}")
        return missing


# Instancia singleton para uso en la aplicación
i18n = I18nManager()


def translate(key: str, **kwargs) -> str:
    """Función de conveniencia para traducir una clave."""
    return i18n.translate(key, **kwargs)
