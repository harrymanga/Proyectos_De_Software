"""Parche CRLF->LF del stdio del MCP SDK en Windows (extraído de mcp_cheatengine.py).

El MCP SDK usa TextIOWrapper sin newline='\\n' y Windows emite CRLF,
lo que rompe JSON-RPC ("invalid trailing data"). Este módulo aplica el
parche ANTES de importar FastMCP. En no-Windows es no-op testeable.
"""

from __future__ import annotations

import sys


def apply_stdio_patch() -> bool:
    """Aplica el parche. Devuelve True si se aplicó (win32), False si no-op."""
    if sys.platform != "win32":
        return False
    import msvcrt
    import os
    from contextlib import asynccontextmanager
    from io import TextIOWrapper

    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    import anyio
    import anyio.lowlevel
    import mcp.server.stdio as mcp_stdio
    import mcp.types as types
    from mcp.shared.message import SessionMessage

    @asynccontextmanager
    async def _patched_stdio_server(
        stdin: anyio.AsyncFile[str] | None = None,
        stdout: anyio.AsyncFile[str] | None = None,
    ):
        if not stdin:
            stdin = anyio.wrap_file(TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline="\n"))
        if not stdout:
            stdout = anyio.wrap_file(
                TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
            )

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def stdin_reader():
            try:
                async with read_stream_writer:
                    async for line in stdin:
                        try:
                            message = types.JSONRPCMessage.model_validate_json(line)
                        except Exception as exc:
                            await read_stream_writer.send(exc)
                            continue
                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async def stdout_writer():
            try:
                async with write_stream_reader:
                    async for session_message in write_stream_reader:
                        json_str = session_message.message.model_dump_json(
                            by_alias=True, exclude_none=True
                        )
                        await stdout.write(json_str + "\n")
                        await stdout.flush()
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async with anyio.create_task_group() as tg:
            tg.start_soon(stdin_reader)
            tg.start_soon(stdout_writer)
            yield read_stream, write_stream

    mcp_stdio.stdio_server = _patched_stdio_server
    try:
        import mcp.server.fastmcp.server as fastmcp_server

        fastmcp_server.stdio_server = _patched_stdio_server
    except ImportError:
        pass
    return True
