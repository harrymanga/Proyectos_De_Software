"""Protocolo del bridge CE: framing LE32+JSON y parseo de env (puro, sin I/O)."""

from __future__ import annotations

import math
import struct

PIPE_NAME = r"\\.\pipe\CE_MCP_Bridge_v99"
MCP_SERVER_NAME = "cheatengine"

# Límite único de trama (antes duplicado en 3 ficheros; hoy 32MB en todos).
MAX_FRAME_SIZE_BYTES = 32 * 1024 * 1024

DEFAULT_TCP_HOST = "127.0.0.1"
DEFAULT_TCP_PORT = 9876
DEFAULT_TIMEOUT_SECONDS = 30.0
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def pack_frame(payload: bytes) -> bytes:
    return struct.pack("<I", len(payload)) + payload


def unpack_frame_size(header: bytes) -> int:
    if len(header) != 4:
        raise ValueError(f"Header debe ser 4 bytes, recibidos {len(header)}")
    return struct.unpack("<I", header)[0]


def validate_frame_size(size: int, direction: str = "frame") -> None:
    if size > MAX_FRAME_SIZE_BYTES:
        raise ConnectionError(
            f"{direction} frame too large: {size} bytes (max {MAX_FRAME_SIZE_BYTES} bytes)."
        )


def is_loopback_host(host: str) -> bool:
    return host in LOOPBACK_HOSTS


def parse_timeout_seconds(raw_value: object) -> float | None:
    """Parse CE_MCP_TIMEOUT seconds; <=0 disables timeout."""
    if raw_value is None:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw_value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    if not math.isfinite(timeout):
        return DEFAULT_TIMEOUT_SECONDS
    if timeout <= 0:
        return None
    return timeout


def parse_transport(raw_value: object) -> str:
    """Parse CE_MCP_TRANSPORT; defaults to Windows named pipe."""
    transport = str(raw_value or "pipe").strip().lower()
    aliases = {
        "named_pipe": "pipe",
        "named-pipe": "pipe",
        "np": "pipe",
        "socket": "tcp",
    }
    transport = aliases.get(transport, transport)
    if transport not in {"pipe", "tcp"}:
        raise ValueError("CE_MCP_TRANSPORT must be 'pipe' or 'tcp'.")
    return transport


def parse_tcp_port(raw_value: object) -> int:
    """Parse CE_MCP_PORT as a TCP port number."""
    if raw_value is None or str(raw_value).strip() == "":
        return DEFAULT_TCP_PORT
    try:
        port = int(str(raw_value).strip())  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError("CE_MCP_PORT must be an integer TCP port.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("CE_MCP_PORT must be between 1 and 65535.")
    return port


def parse_tcp_host(raw_value: object) -> str:
    host = str(raw_value or DEFAULT_TCP_HOST).strip() or DEFAULT_TCP_HOST
    return host
