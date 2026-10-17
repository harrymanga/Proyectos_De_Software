import re
from typing import List

from traductor_pro.domain.interfaces import PlaceholderProtectorPort


class RegexPlaceholderProtector(PlaceholderProtectorPort):
    PATTERN = re.compile(r"\\.|<[^>]+>|%[sd]|\{[^}]+\}|\[[^\]]+\]")

    def __init__(self) -> None:
        self._placeholders: List[str] = []

    def protect(self, text: str) -> str:
        self._placeholders = self.PATTERN.findall(text)
        for i, ph in enumerate(self._placeholders):
            text = text.replace(ph, f"⟦{i}⟧", 1)
        return text

    def restore(self, text: str) -> str:
        for i, ph in enumerate(self._placeholders):
            text = text.replace(f"⟦{i}⟧", ph)
        self._placeholders = []
        return text
