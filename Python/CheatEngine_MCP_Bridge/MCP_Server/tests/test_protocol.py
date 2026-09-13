"""Unitarios del framing LE32+JSON y parsers de env (sin CE, sin red)."""

import struct

import pytest

from MCP_Server.protocol import (
    DEFAULT_TCP_HOST,
    DEFAULT_TCP_PORT,
    MAX_FRAME_SIZE_BYTES,
    PIPE_NAME,
    is_loopback_host,
    pack_frame,
    parse_tcp_host,
    parse_tcp_port,
    parse_timeout_seconds,
    parse_transport,
    unpack_frame_size,
    validate_frame_size,
)


def test_constants():
    assert PIPE_NAME == r"\\.\pipe\CE_MCP_Bridge_v99"
    assert MAX_FRAME_SIZE_BYTES == 32 * 1024 * 1024
    assert (DEFAULT_TCP_HOST, DEFAULT_TCP_PORT) == ("127.0.0.1", 9876)


def test_frame_roundtrip():
    body = b'{"success": true}'
    frame = pack_frame(body)
    assert frame == struct.pack("<I", len(body)) + body
    assert unpack_frame_size(frame[:4]) == len(body)


def test_unpack_bad_header():
    with pytest.raises(ValueError):
        unpack_frame_size(b"\x01\x02")


def test_validate_frame_size_ok_and_limit():
    validate_frame_size(0, "request")
    validate_frame_size(MAX_FRAME_SIZE_BYTES, "request")
    with pytest.raises(ConnectionError):
        validate_frame_size(MAX_FRAME_SIZE_BYTES + 1, "request")


def test_parse_transport():
    assert parse_transport(None) == "pipe"
    assert parse_transport("pipe") == "pipe"
    assert parse_transport("TCP") == "tcp"
    assert parse_transport("socket") == "tcp"
    assert parse_transport("named_pipe") == "pipe"
    assert parse_transport("np") == "pipe"
    with pytest.raises(ValueError):
        parse_transport("udp")


def test_parse_tcp_port():
    assert parse_tcp_port(None) == 9876
    assert parse_tcp_port("") == 9876
    assert parse_tcp_port(" 9876 ") == 9876
    assert parse_tcp_port(1234) == 1234
    with pytest.raises(ValueError):
        parse_tcp_port("abc")
    with pytest.raises(ValueError):
        parse_tcp_port("0")
    with pytest.raises(ValueError):
        parse_tcp_port("70000")


def test_parse_timeout():
    assert parse_timeout_seconds(None) == 30.0
    assert parse_timeout_seconds("10") == 10.0
    assert parse_timeout_seconds("0") is None
    assert parse_timeout_seconds("-5") is None
    assert parse_timeout_seconds("xx") == 30.0
    assert parse_timeout_seconds("inf") == 30.0


def test_parse_host_and_loopback():
    assert parse_tcp_host(None) == "127.0.0.1"
    assert parse_tcp_host("  ") == "127.0.0.1"
    assert parse_tcp_host("192.168.1.5") == "192.168.1.5"
    assert is_loopback_host("127.0.0.1")
    assert is_loopback_host("localhost")
    assert not is_loopback_host("0.0.0.0")
