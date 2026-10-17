import json
import re
from typing import Any, List, Tuple

from traductor_pro.domain.entities import FileType, ParsedLine
from traductor_pro.domain.interfaces import FileHandlerPort


class JsonFileHandler(FileHandlerPort):
    """Archivos .json: traduce hojas string preservando estructura y tipos.

    La clave de cada línea es la ruta JSON serializada (p. ej. '["menu",
    "file"]'), lo que soporta objetos anidados y arreglos. Números,
    booleanos, nulos y strings vacíos no se traducen y se reconstruyen
    con su tipo original. Placeholders ({0}, %s, ${var}).
    """

    PLACEHOLDER_PATTERN = re.compile(r"\\.|\{[^}]*\}|\%[sd]|\$\{[^}]+\}|\[[^\]]+\]")
    _newline = "\n"

    def supported_type(self) -> FileType:
        return FileType.JSON

    def detect_type(self, path: str) -> bool:
        return path.lower().endswith(".json")

    def _collect(self, node: Any, path: List, out: List[Tuple[str, Any]]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                self._collect(value, path + [key], out)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                self._collect(value, path + [index], out)
        else:
            out.append((json.dumps(path, ensure_ascii=False), node))

    def read(self, path: str) -> List[ParsedLine]:
        with open(path, "rb") as _fb:
            if b"\r\n" in _fb.read(4096):
                self._newline = "\r\n"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        leaves: List[Tuple[str, Any]] = []
        self._collect(data, [], leaves)
        lines: List[ParsedLine] = []
        for num, (key, value) in enumerate(leaves, start=1):
            if isinstance(value, str) and value.strip():
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=value,
                    is_translatable=True,
                    key=key,
                    value=value,
                    placeholders=self.PLACEHOLDER_PATTERN.findall(value),
                ))
            else:
                lines.append(ParsedLine(
                    line_number=num,
                    raw_content=json.dumps(value, ensure_ascii=False),
                    is_translatable=False,
                    key=key,
                    value=None,
                ))
        return lines

    def _assign(self, root: Any, path: List, value: Any) -> Any:
        head, *rest = path
        if isinstance(head, int):
            assert isinstance(root, list)
            while len(root) <= head:
                root.append(None)
            if not rest:
                root[head] = value
            else:
                nxt = root[head]
                if not isinstance(nxt, (dict, list)):
                    nxt = [] if isinstance(rest[0], int) else {}
                root[head] = self._assign(nxt, rest, value)
            return root
        assert isinstance(root, dict)
        if not rest:
            root[head] = value
            return root
        nxt = root.get(head)
        if not isinstance(nxt, (dict, list)):
            nxt = [] if isinstance(rest[0], int) else {}
        root[head] = self._assign(nxt, rest, value)
        return root

    def write(self, path: str, lines: List[ParsedLine]) -> None:
        root: Any = None
        for line in lines:
            if not line.key:
                continue
            segments = json.loads(line.key)
            if root is None:
                root = [] if segments and isinstance(segments[0], int) else {}
            if line.is_translatable and line.value is not None:
                value: Any = line.value
            else:
                value = json.loads(line.raw_content)
            root = self._assign(root, segments, value)
        if root is None:
            root = {}
        with open(path, "w", encoding="utf-8", newline="") as f:
            content = json.dumps(root, ensure_ascii=False, indent=2) + "\n"
            if self._newline == "\r\n":
                content = content.replace("\n", "\r\n")
            f.write(content)
