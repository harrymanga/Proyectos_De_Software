"""Runtime: descarga y cache de linuxdeploy/appimagetool."""

from appimage_builder.runtime.downloader import download_file
from appimage_builder.runtime.manager import RuntimeManager

__all__ = ["RuntimeManager", "download_file"]
