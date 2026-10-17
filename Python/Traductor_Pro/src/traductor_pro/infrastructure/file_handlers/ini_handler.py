"""Archivos .ini de idiomas (Windows): secciones [X] y pares clave=valor.

Solo se traduce el *valor*. Se preservan intactos:
- cabeceras de sección `[Menu]`
- comentarios `;` y `#`
- la clave (suelen ser IDs numéricos de controles: `1001`, `MessageError4`)
- valores vacíos, sin texto o sin letras (códigos, números, símbolos)

Detecta UTF-8 (con o sin BOM) y, si falla, cp1252: muchos .ini de software
Windows legacy no están en UTF-8. El formato original se conserva al escribir.
"""
import re
from typing import List

from traductor_pro.domain.entities import FileType, ParsedLine
from traductor_pro.domain.interfaces import FileHandlerPort


class IniFileHandler(FileHandlerPort):
    PLACEHOLDER_PATTERN = re.compile(r"\\.|<[^>]+>|%[sd]|\{[^}]+\}|\[[^\]]+\]")
    SECTION_PATTERN = re.compile(r"^\s*\[[^\]]+\]\s*$")
    COMMENT_PATTERN = re.compile(r"^\s*[;#]")
    HAS_LETTERS_PATTERN = re.compile(r"[^\W\d_]", re.UNICODE)

    _ENCODINGS = ("utf-8", "cp1252", "latin-1")

    def __init__(self) -> None:
        self._encoding = "utf-8"
        self._newline = "\n"
        self._bom = False
        self._final_newline = True

    def supported_type(self) -> FileType:
        return FileType.INI

    def detect_type(self, path: str) -> bool:
        return path.lower().endswith(".ini")

    def _detect_encoding(self, raw: bytes) -> str:
        """UTF-8 (con o sin BOM) y, si no decodifica, cp1252/latin-1.

        `utf-8-sig` decodifica archivos sin BOM, así que solo se usa si el
        BOM está presente: si no, escribiría un BOM nuevo en el archivo.
        """
        if raw.startswith(b"\xef\xbb\xbf"):
            self._bom = True
            return "utf-8-sig"
        for enc in self._ENCODINGS:
            try:
                raw.decode(enc)
            except UnicodeDecodeError:
                continue
            return enc
        return "latin-1"

    def read(self, path: str) -> List[ParsedLine]:
        with open(path, "rb") as fb:
            data = fb.read()
        self._encoding = self._detect_encoding(data)
        self._newline = "\r\n" if b"\r\n" in data else "\n"
        self._final_newline = data.endswith((b"\n", b"\r"))

        lines: List[ParsedLine] = []
        for num, stripped in enumerate(
            data.decode(self._encoding).splitlines(), start=1
        ):
            if (
                not stripped.strip()
                or self.SECTION_PATTERN.match(stripped)
                or self.COMMENT_PATTERN.match(stripped)
                or "=" not in stripped
            ):
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=stripped,
                    is_translatable=False,
                ))
                continue

            key, value = stripped.split("=", 1)
            if not self.HAS_LETTERS_PATTERN.search(value):
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=stripped,
                    is_translatable=False,
                ))
                continue

            lines.append(ParsedLine(
                line_number=num,
                raw_content=stripped,
                is_translatable=True,
                key=key,
                value=value,
                placeholders=self.PLACEHOLDER_PATTERN.findall(value),
            ))
        return lines

    def write(self, path: str, lines: List[ParsedLine]) -> None:
        encoding = "utf-8-sig" if self._bom else self._encoding
        with open(path, "w", encoding=encoding, newline="") as f:
            for idx, line in enumerate(lines):
                if line.is_translatable and line.key is not None:
                    content = f"{line.key}={line.value}"
                else:
                    content = f"{line.raw_content}"
                last = idx == len(lines) - 1
                f.write(content if last and not self._final_newline else content + self._newline)