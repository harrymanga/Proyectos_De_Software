"""Unitarios del relay TCP sin Windows: se stubbean win32file/pywintypes."""

import socket
import struct
import sys
import types

import pytest


def _install_win_stubs():
    if "win32file" not in sys.modules:
        win32file = types.ModuleType("win32file")
        win32file.GENERIC_READ = 0x80000000
        win32file.GENERIC_WRITE = 0x40000000
        win32file.OPEN_EXISTING = 3
        win32file.CreateFile = lambda *_a, **_k: object()
        win32file.ReadFile = lambda _h, _n: (0, b"")
        win32file.WriteFile = lambda _h, _b: None
        win32file.CloseHandle = lambda _h: None
        sys.modules["win32file"] = win32file
    if "pywintypes" not in sys.modules:
        pywintypes = types.ModuleType("pywintypes")
        pywintypes.error = type("error", (OSError,), {})
        sys.modules["pywintypes"] = pywintypes


_install_win_stubs()

from MCP_Server.ce_tcp_relay import (  # noqa: E402
    DEFAULT_HOST,
    DEFAULT_PORT,
    PIPE_NAME,
    parse_args,
    read_socket_exact,
    validate_frame_size,
)


def test_relay_constants_share_protocol():
    from MCP_Server.protocol import (
        DEFAULT_TCP_HOST,
        DEFAULT_TCP_PORT,
    )
    from MCP_Server.protocol import (
        PIPE_NAME as PROTO_PIPE,
    )

    assert (DEFAULT_HOST, DEFAULT_PORT) == (DEFAULT_TCP_HOST, DEFAULT_TCP_PORT)
    assert PIPE_NAME == PROTO_PIPE


def test_read_socket_exact_ok():
    a, b = socket.socketpair()
    try:
        b.sendall(b"hola mundo")
        assert read_socket_exact(a, 10) == b"hola mundo"
    finally:
        a.close()
        b.close()


def test_read_socket_exact_clean_disconnect():
    a, b = socket.socketpair()
    b.close()
    try:
        assert read_socket_exact(a, 4) is None
    finally:
        a.close()


def test_read_socket_exact_mid_frame_disconnect():
    a, b = socket.socketpair()
    try:
        b.sendall(b"ab")
        b.close()
        with pytest.raises(ConnectionError):
            read_socket_exact(a, 10)
    finally:
        a.close()


def test_read_socket_exact_framed():
    body = b'{"id": 1}'
    a, b = socket.socketpair()
    try:
        b.sendall(struct.pack("<I", len(body)) + body)
        header = read_socket_exact(a, 4)
        assert header is not None
        size = struct.unpack("<I", header)[0]
        validate_frame_size(size, "request")
        assert read_socket_exact(a, size) == body
    finally:
        a.close()
        b.close()


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ce_tcp_relay.py"])
    args = parse_args()
    assert (args.host, args.port) == ("127.0.0.1", 9876)


def test_parse_args_custom(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ce_tcp_relay.py", "--host", "127.0.0.1", "--port", "9999"])
    args = parse_args()
    assert (args.host, args.port) == ("127.0.0.1", 9999)
