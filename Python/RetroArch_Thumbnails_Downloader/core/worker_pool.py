"""WorkerPool con context manager."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class WorkerPool:
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def map(self, func: Callable[[T], R], items: Iterable[T]) -> List[R]:
        items = list(items)
        if not items:
            return []
        return list(self.executor.map(func, items))

    def close(self) -> None:
        self.executor.shutdown(wait=True)

    def __enter__(self) -> "WorkerPool":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
