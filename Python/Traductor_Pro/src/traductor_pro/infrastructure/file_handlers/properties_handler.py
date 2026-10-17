import re
from typing import List

from traductor_pro.domain.entities import FileType, ParsedLine
from traductor_pro.domain.interfaces import FileHandlerPort


class PropertiesFileHandler(FileHandlerPort):
    _newline = "\n"
    """Archivos .properties (Java): clave=valor con comentarios #/!.

    Separa en el primer '=' o ':' no escapado; preserva comentarios,
    líneas en blanco y placeholders ({0}, %s, ${var}).
    """

    PLACEHOLDER_PATTERN = re.compile(r"\\.|\{[^}]*\}|\%[sd]|\$\{[^}]+\}|\[[^\]]+\]")
    SEPARATOR_PATTERN = re.compile(r"(?<!\\)[=:]")

    def supported_type(self) -> FileType:
        return FileType.PROPERTIES

    def detect_type(self, path: str) -> bool:
        return path.lower().endswith(".properties")

    def _split(self, raw: str):
        match = self.SEPARATOR_PATTERN.search(raw)
        if not match:
            return None, None
        pos = match.start()
        return raw[:pos], raw[pos + 1:]

    def read(self, path: str) -> List[ParsedLine]:
        with open(path, "rb") as _fb:
            if b"\r\n" in _fb.read(4096):
                self._newline = "\r\n"
        lines: List[ParsedLine] = []
        with open(path, "r", encoding="utf-8") as f:
            for num, raw in enumerate(f, start=1):
                stripped = raw.rstrip("\n\r")
                if not stripped.strip() or stripped.lstrip().startswith(("#", "!")):
                    lines.append(ParsedLine(
                        line_number=num,
                        raw_content=stripped,
                        is_translatable=False,
                    ))
                    continue
                key, value = self._split(stripped)
                if key is None:
                    lines.append(ParsedLine(
                        line_number=num,
                        raw_content=stripped,
                        is_translatable=False,
                    ))
                    continue
                placeholders = self.PLACEHOLDER_PATTERN.findall(value)
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=stripped,
                    is_translatable=True,
                    key=key,
                    value=value,
                    placeholders=placeholders,
                ))
        return lines

    def write(self, path: str, lines: List[ParsedLine]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.is_translatable and line.key is not None:
                    f.write(f"{line.key}={line.value}" + self._newline)
                else:
                    f.write(f"{line.raw_content}" + self._newline)
