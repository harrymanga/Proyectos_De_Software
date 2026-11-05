"""Gestor de archivos para mods de Factorio.

Permite crear, editar, renombrar archivos y carpetas dentro de un mod,
similar a un explorador de archivos tipo VS Code.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from src.core.logger import get_logger
from src.core.security import SecurityError

logger = get_logger(__name__)


class ModFileManager:
    """Gestor de operaciones de archivo para mods de Factorio."""

    def __init__(self, mod_path: Path) -> None:
        """Inicializa el gestor de archivos para un mod."""
        self.mod_path = Path(mod_path).resolve()

    def _resolve_path(self, relative_path: str) -> Path:
        """Resuelve una ruta relativa a absoluta, validando seguridad."""
        target = (self.mod_path / relative_path).resolve()
        mod_resolved = self.mod_path.resolve()
        # Prevenir path traversal
        if not str(target).startswith(str(mod_resolved) + "/") and target != mod_resolved:
            raise SecurityError(f"Ruta no permitida: {relative_path}")
        return target

    def create_file(self, relative_path: str, content: str = "") -> None:
        """Crea un nuevo archivo en el mod.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
            content: Contenido inicial del archivo.
        """
        target = self._resolve_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info("Archivo creado: %s", target)

    def create_folder(self, relative_path: str) -> None:
        """Crea una nueva carpeta en el mod.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        logger.info("Carpeta creada: %s", target)

    def delete_file(self, relative_path: str) -> None:
        """Elimina un archivo del mod.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {relative_path}")
        if target.is_dir():
            raise IsADirectoryError(f"Es una carpeta, no un archivo: {relative_path}")
        target.unlink()
        logger.info("Archivo eliminado: %s", target)

    def delete_folder(self, relative_path: str) -> None:
        """Elimina una carpeta del mod y todo su contenido.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"Carpeta no encontrada: {relative_path}")
        if not target.is_dir():
            raise NotADirectoryError(f"No es una carpeta: {relative_path}")
        shutil.rmtree(target)
        logger.info("Carpeta eliminada: %s", target)

    def rename_file(self, old_path: str, new_path: str) -> None:
        """Renombra un archivo del mod.

        Args:
            old_path: Ruta relativa actual del archivo.
            new_path: Nueva ruta relativa del archivo.
        """
        old_target = self._resolve_path(old_path)
        new_target = self._resolve_path(new_path)

        if not old_target.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {old_path}")

        new_target.parent.mkdir(parents=True, exist_ok=True)
        old_target.rename(new_target)
        logger.info("Archivo renombrado: %s -> %s", old_path, new_path)

    def rename_folder(self, old_path: str, new_path: str) -> None:
        """Renombra una carpeta del mod.

        Args:
            old_path: Ruta relativa actual de la carpeta.
            new_path: Nueva ruta relativa de la carpeta.
        """
        old_target = self._resolve_path(old_path)
        new_target = self._resolve_path(new_path)

        if not old_target.exists():
            raise FileNotFoundError(f"Carpeta no encontrada: {old_path}")

        new_target.parent.mkdir(parents=True, exist_ok=True)
        old_target.rename(new_target)
        logger.info("Carpeta renombrada: %s -> %s", old_path, new_path)

    def list_files(self, relative_path: str = "") -> list[dict[str, Any]]:
        """Lista archivos y carpetas en una ruta relativa.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        if not target.exists() or not target.is_dir():
            return []

        items: list[dict[str, Any]] = []
        for item in sorted(target.iterdir()):
            items.append({
                "name": item.name,
                "path": str(item.relative_to(self.mod_path)),
                "is_dir": item.is_dir(),
                "suffix": item.suffix if item.is_file() else "",
            })
        return items

    def get_file_content(self, relative_path: str) -> str:
        """Lee el contenido de un archivo.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {relative_path}")
        return target.read_text(encoding="utf-8")

    def write_file_content(self, relative_path: str, content: str) -> None:
        """Escribe contenido a un archivo.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
            content: Contenido a escribir.
        """
        target = self._resolve_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info("Archivo guardado: %s", target)

    def get_file_list_tree(self, relative_path: str = "") -> list[dict[str, Any]]:
        """Obtiene la lista de archivos en forma de árbol jerárquico.

        Args:
            relative_path: Ruta relativa desde la carpeta del mod.
        """
        target = self._resolve_path(relative_path)
        if not target.exists() or not target.is_dir():
            return []

        items: list[dict[str, Any]] = []
        for item in sorted(target.iterdir()):
            item_info: dict[str, Any] = {
                "name": item.name,
                "path": str(item.relative_to(self.mod_path)),
                "is_dir": item.is_dir(),
                "suffix": item.suffix if item.is_file() else "",
                "children": [],
            }
            if item.is_dir():
                item_info["children"] = self.get_file_list_tree(str(item.relative_to(self.mod_path)))
            items.append(item_info)
        return items
