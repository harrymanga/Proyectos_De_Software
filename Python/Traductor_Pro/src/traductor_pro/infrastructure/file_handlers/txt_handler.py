from typing import List

from traductor_pro.domain.entities import FileType, ParsedLine
from traductor_pro.domain.interfaces import FileHandlerPort


class TxtFileHandler(FileHandlerPort):
    _newline = "\n"
    def supported_type(self) -> FileType:
        return FileType.TXT

    def detect_type(self, path: str) -> bool:
        return path.lower().endswith(".txt")

    def read(self, path: str) -> List[ParsedLine]:
        with open(path, "rb") as _fb:
            if b"\r\n" in _fb.read(4096):
                self._newline = "\r\n"
        lines: List[ParsedLine] = []
        with open(path, "r", encoding="utf-8") as f:
            for num, raw in enumerate(f, start=1):
                raw = raw.rstrip("\n\r")
                is_translatable = len(raw.strip()) > 0
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=raw,
                    is_translatable=is_translatable,
                    value=raw if is_translatable else None,
                ))
        return lines

    def write(self, path: str, lines: List[ParsedLine]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.is_translatable and line.value is not None:
                    f.write(f"{line.value}\n")
                else:
                    f.write(f"{line.raw_content}" + self._newline)
