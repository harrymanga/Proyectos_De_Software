"""Descarga atómica de archivos con httpx + filelock."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
from filelock import FileLock

from appimage_builder.core.exceptions import DownloadError

ProgressFn = Callable[[int, int | None], Awaitable[None]] | None


async def download_file(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 120.0,
    progress: ProgressFn = None,
) -> Path:
    """Descarga `url` a `dest` de forma atómica (vía `.part` + rename).

    Usa un filelock (`dest.with_suffix(dest.suffix + '.lock')`) para evitar
    descargas concurrentes del mismo archivo. Si `dest` ya existe y no está
    vacío, se reutiliza sin descargar.

    Raises:
        DownloadError: si la descarga falla (red, HTTP, IO).
    """
    dest = dest.expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size > 0:
        return dest

    lock_path = dest.with_name(dest.name + ".lock")
    tmp_path = dest.with_name(dest.name + ".part")
    lock = FileLock(str(lock_path))

    try:
        with lock:
            # Re-chequear dentro del lock (otro proceso pudo terminar).
            if dest.exists() and dest.stat().st_size > 0:
                return dest
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, timeout=timeout, headers=headers
                ) as client:
                    async with client.stream("GET", url) as resp:
                        if resp.status_code >= 400:
                            raise DownloadError(
                                f"Descarga fallida (HTTP {resp.status_code})",
                                url=url,
                                destination=dest,
                                status_code=resp.status_code,
                            )
                        total: int | None = None
                        content_length = resp.headers.get("content-length")
                        if content_length and content_length.isdigit():
                            total = int(content_length)
                        downloaded = 0
                        with tmp_path.open("wb") as f:
                            async for chunk in resp.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress is not None:
                                    await progress(downloaded, total)
            except DownloadError:
                raise
            except Exception as e:
                raise DownloadError(
                    f"No se pudo descargar: {e}",
                    url=url,
                    destination=dest,
                ) from e

            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                raise DownloadError(
                    "Descarga vacía",
                    url=url,
                    destination=dest,
                )
            tmp_path.replace(dest)
            return dest
    finally:
        try:
            if tmp_path.exists() and not dest.exists():
                tmp_path.unlink()
        except OSError:
            pass
