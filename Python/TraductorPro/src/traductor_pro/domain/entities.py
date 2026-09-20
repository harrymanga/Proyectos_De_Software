from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TranslationEngine(Enum):
    GOOGLE = "google"
    DEEPL = "deepl"
    OPENAI = "openai"
    TRANSSHELL = "transshell"


class FileType(Enum):
    CFG = "cfg"
    LANG = "lang"
    TXT = "txt"
    PROPERTIES = "properties"
    JSON = "json"


@dataclass(frozen=True)
class TranslationRequest:
    source_text: str
    target_lang: str
    engine: TranslationEngine
    source_lang: Optional[str] = None


@dataclass
class TranslationResult:
    translated_text: str
    success: bool
    from_cache: bool = False
    error: Optional[str] = None


@dataclass
class ParsedLine:
    line_number: int
    raw_content: str
    is_translatable: bool
    key: Optional[str] = None
    value: Optional[str] = None
    placeholders: List[str] = field(default_factory=list)


@dataclass
class FileTranslationJob:
    input_path: str
    output_path: str
    file_type: FileType
    target_lang: str
    engine: TranslationEngine
    source_lang: Optional[str] = None
    custom_replacements: Dict[str, str] = field(default_factory=dict)
    protect_placeholders: bool = True
    backup_original: bool = True


@dataclass
class TranslationReport:
    input_path: str
    output_path: str
    engine: TranslationEngine
    target_lang: str
    total_lines: int = 0
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    cached: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class GlobalReport:
    reports: List[TranslationReport] = field(default_factory=list)
    timestamp: str = ""

    @property
    def total_files(self) -> int:
        return len(self.reports)

    @property
    def total_attempted(self) -> int:
        return sum(r.attempted for r in self.reports)

    @property
    def total_succeeded(self) -> int:
        return sum(r.succeeded for r in self.reports)

    @property
    def total_failed(self) -> int:
        return sum(r.failed for r in self.reports)

    @property
    def total_cached(self) -> int:
        return sum(r.cached for r in self.reports)
