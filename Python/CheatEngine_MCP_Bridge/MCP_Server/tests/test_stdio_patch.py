"""stdio_patch es no-op fuera de Windows y no rompe stdio."""

import sys

from MCP_Server import stdio_patch


def test_noop_off_windows():
    if sys.platform == "win32":
        assert stdio_patch.apply_stdio_patch() is True
    else:
        assert stdio_patch.apply_stdio_patch() is False


def test_stdio_intact_after_import():
    # El parche no debe redirigir stdout (solo mcp_cheatengine lo hace en runtime)
    assert sys.stdout is not sys.stderr
