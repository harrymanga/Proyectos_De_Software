import hashlib
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

from traductor_pro.domain.entities import (
    FileTranslationJob,
    FileType,
    GlobalReport,
    ParsedLine,
    TranslationEngine,
    TranslationReport,
    TranslationRequest,
    TranslationResult,
)
from traductor_pro.domain.interfaces import (
    CachePort,
    FileHandlerPort,
    KeyManagerPort,
    PlaceholderProtectorPort,
    ProgressCallback,
    ReportGeneratorPort,
    TranslatorPort,
)

logger = logging.getLogger(__name__)


class TranslateTextUseCase:
    def __init__(
        self,
        translator: TranslatorPort,
        cache: CachePort,
        placeholder_protector: PlaceholderProtectorPort,
    ) -> None:
        self._translator = translator
        self._cache = cache
        self._protector = placeholder_protector

    def execute(self, request: TranslationRequest) -> TranslationResult:
        text_to_translate = request.source_text

        if not text_to_translate or not text_to_translate.strip():
            return TranslationResult(translated_text=text_to_translate, success=True)

        protected_text = self._protector.protect(text_to_translate)

        cache_key = self._generate_cache_key(protected_text, request.target_lang, request.engine)
        cached = self._cache.get(cache_key)
        if cached is not None:
            restored = self._protector.restore(cached)
            return TranslationResult(translated_text=restored, success=True, from_cache=True)

        protected_request = TranslationRequest(
            source_text=protected_text,
            target_lang=request.target_lang,
            engine=request.engine,
            source_lang=request.source_lang,
        )

        result = self._translator.translate(protected_request)

        if result.success and result.translated_text:
            self._cache.set(cache_key, result.translated_text)
            result.translated_text = self._protector.restore(result.translated_text)

        return result

    @staticmethod
    def _generate_cache_key(text: str, target_lang: str, engine: TranslationEngine) -> str:
        raw = f"{engine.value}:{target_lang}:{text}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()


class TranslateFileUseCase:
    def __init__(
        self,
        translators: Dict[TranslationEngine, TranslatorPort],
        file_handlers: Dict[FileType, FileHandlerPort],
        cache: CachePort,
        placeholder_protector: PlaceholderProtectorPort,
        report_generator: ReportGeneratorPort,
        key_manager: KeyManagerPort,
    ) -> None:
        self._translators = translators
        self._file_handlers = file_handlers
        self._cache = cache
        self._protector = placeholder_protector
        self._report_generator = report_generator
        self._key_manager = key_manager
        self._translate_text = TranslateTextUseCase(
            translator=None,  # type: ignore
            cache=cache,
            placeholder_protector=placeholder_protector,
        )

    def execute(
        self,
        job: FileTranslationJob,
        progress: Optional[ProgressCallback] = None,
    ) -> TranslationReport:
        report = TranslationReport(
            input_path=job.input_path,
            output_path=job.output_path,
            engine=job.engine,
            target_lang=job.target_lang,
        )

        try:
            if job.backup_original:
                self._backup(job.input_path)

            handler = self._file_handlers.get(job.file_type)
            if handler is None:
                raise ValueError(f"No hay handler para tipo {job.file_type}")

            translator = self._translators.get(job.engine)
            if translator is None:
                raise ValueError(f"No hay traductor para motor {job.engine}")

            self._translate_text = TranslateTextUseCase(
                translator=translator,
                cache=self._cache,
                placeholder_protector=self._protector,
            )

            parsed_lines = handler.read(job.input_path)
            report.total_lines = len(parsed_lines)

            translatable = [line for line in parsed_lines if line.is_translatable]
            report.attempted = len(translatable)

            total = len(translatable)
            for idx, line in enumerate(translatable):
                try:
                    request = TranslationRequest(
                        source_text=line.value or "",
                        target_lang=job.target_lang,
                        engine=job.engine,
                        source_lang=job.source_lang,
                    )

                    result = self._translate_text.execute(request)

                    if result.success:
                        translated = result.translated_text
                        if job.custom_replacements:
                            translated = self._apply_replacements(translated, job.custom_replacements)
                        line.value = translated
                        report.succeeded += 1
                        if result.from_cache:
                            report.cached += 1
                    else:
                        report.failed += 1
                        if result.error:
                            report.errors.append(f"Línea {line.line_number}: {result.error}")

                except Exception as e:
                    report.failed += 1
                    report.errors.append(f"Línea {line.line_number}: {str(e)}")
                    logger.error("Error traduciendo línea %d: %s", line.line_number, e)

                if progress:
                    progress.on_progress(idx + 1, total, f"Traduciendo línea {idx + 1} de {total}")

            handler.write(job.output_path, parsed_lines)

        except Exception as e:
            report.errors.append(str(e))
            logger.error("Error procesando archivo %s: %s", job.input_path, e)
            if progress:
                progress.on_error(str(e))

        if progress:
            progress.on_file_complete(report)

        return report

    @staticmethod
    def _backup(path: str) -> None:
        from traductor_pro.infrastructure.system.app_paths import backups_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parent_hash = hashlib.md5(os.path.dirname(path).encode("utf-8")).hexdigest()[:8]
        base = os.path.basename(path)
        name, ext = os.path.splitext(base)
        backup_path = os.path.join(backups_dir(), f"{name}_{timestamp}_{parent_hash}{ext}")
        shutil.copy2(path, backup_path)
        logger.info("Backup creado: %s", backup_path)

    @staticmethod
    def _apply_replacements(text: str, replacements: Dict[str, str]) -> str:
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text


class TranslateBatchUseCase:
    def __init__(self, translate_file: TranslateFileUseCase) -> None:
        self._translate_file = translate_file

    def execute(
        self,
        jobs: List[FileTranslationJob],
        progress: Optional[ProgressCallback] = None,
    ) -> GlobalReport:
        global_report = GlobalReport(timestamp=datetime.now().isoformat())

        for idx, job in enumerate(jobs):
            if progress:
                progress.on_progress(idx + 1, len(jobs), f"Procesando archivo {idx + 1} de {len(jobs)}")

            report = self._translate_file.execute(job, progress)
            global_report.reports.append(report)

        return global_report


class ManageApiKeysUseCase:
    def __init__(self, key_manager: KeyManagerPort) -> None:
        self._key_manager = key_manager

    def get(self, service: str) -> Optional[str]:
        return self._key_manager.get_key(service)

    def set(self, service: str, api_key: str) -> None:
        self._key_manager.set_key(service, api_key)

    def delete(self, service: str) -> None:
        self._key_manager.delete_key(service)
