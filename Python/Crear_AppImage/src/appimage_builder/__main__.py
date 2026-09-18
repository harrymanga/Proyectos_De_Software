"""Entry point `python -m appimage_builder` y console-script."""

from __future__ import annotations

from appimage_builder.cli.main import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
