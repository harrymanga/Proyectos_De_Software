from abc import ABC, abstractmethod
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


class TranslatorPort(ABC):
    @abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        pass


class FileHandlerPort(ABC):
    @abstractmethod
    def supported_type(self) -> FileType:
        pass

    @abstractmethod
    def read(self, path: str) -> List[ParsedLine]:
        pass

    @abstractmethod
    def write(self, path: str, lines: List[ParsedLine]) -> None:
        pass

    @abstractmethod
    def detect_type(self, path: str) -> bool:
        pass


class CachePort(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class KeyManagerPort(ABC):
    @abstractmethod
    def get_key(self, service: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_key(self, service: str, api_key: str) -> None:
        pass

    @abstractmethod
    def delete_key(self, service: str) -> None:
        pass


class PlaceholderProtectorPort(ABC):
    @abstractmethod
    def protect(self, text: str) -> str:
        pass

    @abstractmethod
    def restore(self, text: str) -> str:
        pass


class ReportGeneratorPort(ABC):
    @abstractmethod
    def generate(self, report: GlobalReport) -> str:
        pass

    @abstractmethod
    def save(self, report: GlobalReport, path: str) -> None:
        pass


class ProgressCallback(ABC):
    @abstractmethod
    def on_progress(self, current: int, total: int, message: str) -> None:
        pass

    @abstractmethod
    def on_file_complete(self, report: TranslationReport) -> None:
        pass

    @abstractmethod
    def on_error(self, error: str) -> None:
        pass
