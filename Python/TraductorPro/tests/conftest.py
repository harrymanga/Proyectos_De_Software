import os
import tempfile

import pytest

from traductor_pro.domain.entities import (
    FileTranslationJob,
    FileType,
    TranslationEngine,
    TranslationReport,
)
from traductor_pro.domain.interfaces import (
    CachePort,
    FileHandlerPort,
    KeyManagerPort,
    PlaceholderProtectorPort,
    TranslatorPort,
)
from traductor_pro.domain.entities import TranslationRequest, TranslationResult


# --- Fakes / Stubs para pruebas ---


class FakeTranslator(TranslatorPort):
    def __init__(self, prefix: str = "TR_") -> None:
        self._prefix = prefix
        self.call_count = 0

    def translate(self, request: TranslationRequest) -> TranslationResult:
        self.call_count += 1
        translated = f"{self._prefix}{request.source_text}"
        return TranslationResult(translated_text=translated, success=True)


class FakeCache(CachePort):
    def __init__(self) -> None:
        self._store: dict = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value

    def exists(self, key: str) -> bool:
        return key in self._store

    def clear(self) -> None:
        self._store.clear()


class FakeKeyManager(KeyManagerPort):
    def __init__(self) -> None:
        self._keys: dict = {}

    def get_key(self, service: str):
        return self._keys.get(service)

    def set_key(self, service: str, api_key: str) -> None:
        self._keys[service] = api_key

    def delete_key(self, service: str) -> None:
        self._keys.pop(service, None)


class FakePlaceholderProtector(PlaceholderProtectorPort):
    def __init__(self) -> None:
        self._placeholders: list = []

    def protect(self, text: str) -> str:
        import re
        pattern = re.compile(r"<[^>]+>|%[sd]|\{[^}]+\}")
        self._placeholders = pattern.findall(text)
        result = text
        for i, ph in enumerate(self._placeholders):
            result = result.replace(ph, f"⟦{i}⟧", 1)
        return result

    def restore(self, text: str) -> str:
        result = text
        for i, ph in enumerate(self._placeholders):
            result = result.replace(f"⟦{i}⟧", ph)
        self._placeholders = []
        return result


class FakeReportGenerator:
    def generate(self, report) -> str:
        return f"Report: {report.total_files} files"

    def save(self, report, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "test_report.txt"), "w") as f:
            f.write(self.generate(report))


# --- Fixtures ---


@pytest.fixture
def fake_translator():
    return FakeTranslator()


@pytest.fixture
def fake_cache():
    return FakeCache()


@pytest.fixture
def fake_key_manager():
    return FakeKeyManager()


@pytest.fixture
def fake_protector():
    return FakePlaceholderProtector()


@pytest.fixture
def fake_report_gen():
    return FakeReportGenerator()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_cfg_file(tmp_dir):
    path = os.path.join(tmp_dir, "test.cfg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("key1=Hello World\n")
        f.write("# comment\n")
        f.write("key2=Goodbye\n")
    return path


@pytest.fixture
def sample_lang_file(tmp_dir):
    path = os.path.join(tmp_dir, "test.lang")
    with open(path, "w", encoding="utf-8") as f:
        f.write('msg.hello=Hello <player>\n')
        f.write('msg.count=You have %s items\n')
        f.write('msg.bye=Goodbye\n')
    return path


@pytest.fixture
def sample_txt_file(tmp_dir):
    path = os.path.join(tmp_dir, "test.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("Hello World\n")
        f.write("\n")
        f.write("This is a test\n")
    return path


@pytest.fixture
def sample_properties_file(tmp_dir):
    path = os.path.join(tmp_dir, "test.properties")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# comment\n")
        f.write("greeting=Hello {0}\n")
        f.write("farewell:Goodbye %s\n")
        f.write("! another comment\n")
    return path


@pytest.fixture
def sample_json_file(tmp_dir):
    path = os.path.join(tmp_dir, "test.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"menu": {"file": "Open {0}", "edit": "Edit"}, '
                '"count": 3, "active": true, "nothing": null, '
                '"items": ["First %s", ""], "empty": ""}')
    return path
