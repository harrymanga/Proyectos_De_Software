"""Workers en QThread (Fase 5; la UI los consume en Fase 6)."""

from appimage_builder.gui.workers.build_worker import BuildWorker

__all__ = ["BuildWorker"]
