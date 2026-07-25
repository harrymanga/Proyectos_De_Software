#!/usr/bin/env python3
r"""Retransmisión de TCP a canalización con nombre para el puente MCP de Cheat Engine.

Ejecute este script en Windows mientras ``ce_mcp_bridge.lua`` está cargado en Cheat Engine. Acepta tramas JSON-RPC con prefijo de la misma longitud utilizadas por
``mcp_cheatengine.py`` y los reenvía a ``\\.\pipe\CE_MCP_Bridge_v99``

Utilícelo cuando el servidor MCP no pueda abrir la canalización con nombre de Windows directamente, como
como desde WSL, un contenedor u otro host.

Vinculado a 127.0.0.1 a menos que quieras exponer intencionalmente el control de Cheat Engine
a otra maquina.
"""

from __future__ import annotations

import argparse
import socket
import socketserver
import struct
import sys
from typing import Optional

try:
    import pywintypes
    import win32file
except ImportError as exc:  # pragma: no cover - Windows-only helper
    print("ce_tcp_relay.py debe ejecutarse en Windows con pywin32 instalado.", file=sys.stderr)
    raise SystemExit(1) from exc


PIPE_NAME = r"\\.\pipe\CE_MCP_Bridge_v99"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
MAX_FRAME_SIZE_BYTES = 32 * 1024 * 1024


def read_socket_exact(sock: socket.socket, size: int) -> Optional[bytes]:
    """Read exactly size bytes, returning None on clean peer disconnect."""
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            if remaining == size:
                return None
            raise ConnectionError("El cliente TCP se desconectó a mitad del fotograma.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_pipe_exact(handle, size: int) -> bytes:
    """Read exactly size bytes from a Windows named pipe."""
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = win32file.ReadFile(handle, remaining)[1]
        if not chunk:
            raise ConnectionError("Tubo Cheat Engine cerrado en el medio del marco.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def validate_frame_size(size: int, direction: str) -> None:
    if size > MAX_FRAME_SIZE_BYTES:
        raise ConnectionError(
            f"{direction} marco demasiado grande: {size} bytes "
            f"(max {MAX_FRAME_SIZE_BYTES} bytes)."
        )


def open_pipe():
    return win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None,
    )


class RelayHandler(socketserver.BaseRequestHandler):
    """Relay one TCP client connection to one persistent CE pipe connection."""

    pipe_handle = None

    def setup(self) -> None:
        self.pipe_handle = None
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def handle(self) -> None:
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        print(f"[relay] Cliente TCP conectado: {peer}", file=sys.stderr, flush=True)
        try:
            self.pipe_handle = open_pipe()
            while True:
                req_header = read_socket_exact(self.request, 4)
                if req_header is None:
                    break
                req_len = struct.unpack("<I", req_header)[0]
                validate_frame_size(req_len, "request")
                req_body = read_socket_exact(self.request, req_len)
                if req_body is None:
                    raise ConnectionError("Cliente TCP desconectado antes del cuerpo de la solicitud.")

                win32file.WriteFile(self.pipe_handle, req_header)
                win32file.WriteFile(self.pipe_handle, req_body)

                resp_header = read_pipe_exact(self.pipe_handle, 4)
                resp_len = struct.unpack("<I", resp_header)[0]
                validate_frame_size(resp_len, "response")
                resp_body = read_pipe_exact(self.pipe_handle, resp_len)
                self.request.sendall(resp_header + resp_body)
        except pywintypes.error as exc:
            print(f"[relay] Error de canalización de Windows para {peer}: {exc}", file=sys.stderr, flush=True)
        except (ConnectionError, OSError) as exc:
            print(f"[relay] La conexión finalizó por {peer}: {exc}", file=sys.stderr, flush=True)
        finally:
            self._close_pipe()
            print(f"[relay] Cliente TCP desconectado: {peer}", file=sys.stderr, flush=True)

    def _close_pipe(self) -> None:
        if self.pipe_handle is None:
            return
        try:
            win32file.CloseHandle(self.pipe_handle)
        except pywintypes.error:
            pass
        finally:
            self.pipe_handle = None


class RelayServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transmitir tramas TCP a la canalización con nombre de Windows MCP de Cheat Engine."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host de enlace TCP (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Puerto de enlace TCP (default: {DEFAULT_PORT})")
    parser.add_argument("--pipe", default=PIPE_NAME, help=f"Ruta de tubería con nombre (default: {PIPE_NAME})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        print("--port debe estar entre 1 y 65535.", file=sys.stderr)
        return 2

    global PIPE_NAME
    PIPE_NAME = args.pipe

    print(
        f"[relay] Escuchando {args.host}:{args.port}; reenviar a {PIPE_NAME}",
        file=sys.stderr,
        flush=True,
    )
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print(
            "[relay] ADVERTENCIA: el enlace sin bucle invertido expone el control de Cheat Engine a la red.",
            file=sys.stderr,
            flush=True,
        )

    with RelayServer((args.host, args.port), RelayHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[relay] Parada.", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
