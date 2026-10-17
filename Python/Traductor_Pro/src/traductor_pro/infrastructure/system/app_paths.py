"""Rutas del sistema para artefactos de la aplicación.

Criterio: reportes, backups y logs van a la carpeta temporal del sistema
operativo (tempfile.gettempdir) para no aglomerar archivos en los
directorios de trabajo del usuario. La caché se conserva en el home
(~/.traductor_pro/cache) porque tiene valor persistente entre ejecuciones.
"""
import os
import tempfile


def base_temp_dir() -> str:
    """Directorio temporal propio (se crea si no existe)."""
    path = os.path.join(tempfile.gettempdir(), "traductor_pro")
    os.makedirs(path, exist_ok=True)
    return path


def backups_dir() -> str:
    """Backups de originales (temporales del SO)."""
    path = os.path.join(base_temp_dir(), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def reports_dir() -> str:
    """Reportes de traducción (temporales del SO)."""
    path = os.path.join(base_temp_dir(), "reports")
    os.makedirs(path, exist_ok=True)
    return path


def default_cache_dir() -> str:
    """Caché persistente en el home (no es temporal: se reutiliza)."""
    return os.path.join(os.path.expanduser("~"), ".traductor_pro", "cache")
