"""Plugin de Factorio para Mod_Maker.

Factorio distribuye mods como archivos .zip que contienen al menos un archivo
info.json con metadatos y opcionalmente data.lua, data-updates.lua, etc.

Este plugin implementa la interfaz GamePlugin para el juego Factorio,
incluyendo detección de instalación por SO, extracción segura, reconstrucción,
validación de metadatos, instalación/desinstalación con copia de seguridad,
y detección de conflictos de dependencias.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Any

from src.core.security import (
    DANGEROUS_EXTENSIONS,
    SecurityError,
    is_dangerous_extension,
    validate_extraction_target,
    validate_mod_name,
)
from src.plugins.base_plugin import GamePlugin

logger = __import__("src.core.logger", fromlist=["get_logger"]).get_logger(__name__)

INFO_JSON = "info.json"
BACKUP_SUFFIX = ".bak"


class FactorioPlugin(GamePlugin):
    """Plugin de soporte para Factorio."""

    game_id = "factorio"
    game_name = "Factorio"
    supported_extensions = (".zip",)

    # Carpetas típicas de mods de Factorio por sistema operativo (rutas base,
    # sin expandir variables de entorno en tiempo de definición de clase).
    _MODS_FOLDERS: dict[str, list[str]] = {
        "windows": [
            "%APPDATA%/Factorio/mods",
        ],
        "darwin": [
            "~/Library/Application Support/factorio/mods",
        ],
        "linux": [
            "~/factorio/mods",
            "~/.local/share/factorio/mods",
        ],
    }

    def __init__(self) -> None:
        super().__init__()
        self._custom_mods_folder: str | None = None

    # Campos obligatorios en info.json
    _REQUIRED_METADATA_FIELDS = ("name", "version")

    def _resolve_path(self, path_template: str) -> Path:
        """Resuelve una plantilla de ruta expandiendo ~ y variables de entorno."""
        expanded = os.path.expanduser(path_template)
        expanded = os.path.expandvars(expanded)
        return Path(expanded)

    def set_mods_folder(self, folder_path: str) -> None:
        """Establece manualmente la carpeta de mods de Factorio.

        Se usa cuando la detección automática falla y el usuario proporciona
        una ubicación personalizada.
        """
        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"La carpeta no existe o no es válida: {folder_path}")
        self._custom_mods_folder = str(path)
        logger.info("Carpeta de mods configurada manualmente: %s", path)

    def detect_installation(self) -> str | None:
        """Intenta detectar la carpeta de mods de Factorio por sistema operativo.

        Si se configuró una carpeta personalizada, se usa esa directamente.
        De lo contrario, busca en las rutas típicas por SO.
        """
        if self._custom_mods_folder:
            logger.info("Usando carpeta de mods personalizada: %s", self._custom_mods_folder)
            return self._custom_mods_folder
        system = platform.system().lower()
        candidates = self._MODS_FOLDERS.get(system, [])
        for template in candidates:
            folder = self._resolve_path(template)
            if folder.exists() and folder.is_dir():
                logger.info("Factorio detectado en %s", folder)
                return str(folder)
        logger.warning(
            "No se detectó la carpeta de mods de Factorio automáticamente en %s",
            system,
        )
        return None

    def get_mods_folder(self) -> str | None:
        """Devuelve la carpeta de mods de Factorio detectada o configurada."""
        return self.detect_installation()

    def _mods_folder(self) -> Path:
        """Devuelve la carpeta de mods como Path, o lanza SecurityError si no se encuentra."""
        folder = self.get_mods_folder()
        if folder is None:
            raise SecurityError(
                "No se pudo determinar la carpeta de mods de Factorio. "
                "Configúrela manualmente en la aplicación."
            )
        return Path(folder)

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------

    def _find_info_json(self, zip_ref: zipfile.ZipFile) -> str | None:
        """Busca el archivo info.json dentro de un ZIP de forma robusta.

        Busca:
        - Exacto: "info.json"
        - Case-insensitive: "INFO.JSON", "Info.json", etc.
        - Con prefijo de ruta: "./info.json", "folder/info.json", etc.

        Devuelve el nombre exacto del miembro en el ZIP, o None si no se encuentra.
        """
        names = zip_ref.namelist()
        # 1. Búsqueda exacta
        if INFO_JSON in names:
            return INFO_JSON
        # 2. Búsqueda case-insensitive de nombre base
        for name in names:
            base = name.split("/")[-1].split("\\")[-1]
            if base.lower() == INFO_JSON.lower():
                return name
        # 3. Búsqueda de cualquier entrada que termine con /info.json o \info.json
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized.endswith("/" + INFO_JSON) or normalized == INFO_JSON:
                return name
        return None

    def validate(self, mod_path: Path) -> bool:
        """Valida que un archivo .zip sea un mod de Factorio válido.

        Un mod válido es un ZIP que contiene info.json con JSON parseable
        y los campos obligatorios (name, version).
        """
        mod_path = Path(mod_path)
        if not mod_path.exists():
            logger.warning("El archivo no existe: %s", mod_path)
            return False
        if not zipfile.is_zipfile(mod_path):
            logger.warning("El archivo no es un ZIP válido: %s", mod_path)
            return False
        try:
            with zipfile.ZipFile(mod_path, "r") as zip_ref:
                info_member = self._find_info_json(zip_ref)
                if info_member is None:
                    logger.warning("Falta %s en el mod: %s", INFO_JSON, mod_path)
                    return False
                info_data = zip_ref.read(info_member)
                metadata = json.loads(info_data.decode("utf-8"))
                for field in self._REQUIRED_METADATA_FIELDS:
                    if field not in metadata or not str(metadata[field]).strip():
                        logger.warning(
                            "Campo obligatorio '%s' faltante o vacío en %s",
                            field,
                            mod_path,
                        )
                        return False
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("Validación fallida para %s: %s", mod_path, exc)
            return False
        return True

    def get_metadata(self, mod_path: Path) -> dict[str, Any] | None:
        """Lee los metadatos info.json de un mod de Factorio.

        Devuelve None si el mod no es válido o no se pueden leer los metadatos.
        """
        mod_path = Path(mod_path)
        if not self.validate(mod_path):
            return None
        try:
            with zipfile.ZipFile(mod_path, "r") as zip_ref:
                info_member = self._find_info_json(zip_ref)
                if info_member is None:
                    return None
                info_data = zip_ref.read(info_member)
                return json.loads(info_data.decode("utf-8"))
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("No se pudieron leer los metadatos de %s: %s", mod_path, exc)
            return None

    # ------------------------------------------------------------------
    # Extracción y reconstrucción
    # ------------------------------------------------------------------

    def extract(self, mod_path: Path, dest_dir: Path) -> None:
        """Extrae un mod .zip de Factorio a dest_dir con validación de seguridad.

        - Evita path traversal.
        - Bloquea extensiones potencialmente peligrosas.
        - Crea la carpeta de destino si no existe.
        """
        mod_path = Path(mod_path)
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        if not self.validate(mod_path):
            raise SecurityError(f"El archivo no es un mod de Factorio válido: {mod_path}")

        with zipfile.ZipFile(mod_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                member_path = member.filename
                # Evitar directorios absolutos o traversal
                target = validate_extraction_target(dest_dir, member_path)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                # Bloquear extensiones peligrosas
                if is_dangerous_extension(Path(member_path)):
                    logger.warning(
                        "Saltando archivo potencialmente peligroso: %s", member_path
                    )
                    continue
                with zip_ref.open(member) as source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink)
        logger.info("Mod extraído correctamente: %s -> %s", mod_path, dest_dir)

    def build(self, source_dir: Path, output_path: Path) -> None:
        """Empaqueta source_dir como un mod .zip de Factorio en output_path.

        - Requiere info.json en source_dir.
        - Bloquea extensiones potencialmente peligrosas.
        - Crea la carpeta de salida si no existe.
        """
        source_dir = Path(source_dir)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not source_dir.is_dir():
            raise SecurityError(f"La carpeta de origen no existe: {source_dir}")

        info_path = source_dir / INFO_JSON
        if not info_path.exists():
            raise SecurityError(
                f"Falta el archivo {INFO_JSON} en {source_dir}. "
                "Un mod de Factorio requiere info.json."
            )

        # Validar que info.json tenga campos requeridos antes de empaquetar
        try:
            with info_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
            for field in self._REQUIRED_METADATA_FIELDS:
                if field not in metadata or not str(metadata[field]).strip():
                    raise SecurityError(
                        f"info.json carece del campo obligatorio '{field}'."
                    )
        except json.JSONDecodeError as exc:
            raise SecurityError(f"info.json no es un JSON válido: {exc}") from exc

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in sorted(source_dir.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    if is_dangerous_extension(file_path):
                        logger.warning(
                            "Saltando archivo potencialmente peligroso: %s", arcname
                        )
                        continue
                    zip_ref.write(file_path, arcname)
        logger.info("Mod construido correctamente: %s -> %s", source_dir, output_path)

    # ------------------------------------------------------------------
    # Metadatos
    # ------------------------------------------------------------------

    def create_info_json(
        self,
        name: str,
        version: str,
        author: str = "",
        description: str = "",
        factorio_version: str = "1.1",
        dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Crea un diccionario de metadatos info.json para un mod nuevo."""
        validate_mod_name(name)
        if not version or not version.strip():
            raise SecurityError("La versión del mod no puede estar vacía.")
        return {
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "factorio_version": factorio_version,
            "dependencies": dependencies or [],
        }

    def save_info_json(self, source_dir: Path, metadata: dict[str, Any]) -> None:
        """Guarda info.json dentro de la carpeta de origen del mod."""
        source_dir = Path(source_dir)
        source_dir.mkdir(parents=True, exist_ok=True)
        info_path = source_dir / INFO_JSON
        with info_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info("info.json guardado en %s", info_path)

    # ------------------------------------------------------------------
    # Instalación / desinstalación / lista
    # ------------------------------------------------------------------

    def _backup_file(self, file_path: Path) -> Path:
        """Crea una copia de seguridad de un archivo antes de modificarlo.

        Devuelve la ruta de la copia de seguridad.
        """
        backup_path = file_path.with_suffix(file_path.suffix + BACKUP_SUFFIX)
        if backup_path.exists():
            backup_path.unlink()
        shutil.copy2(file_path, backup_path)
        logger.info("Copia de seguridad creada: %s", backup_path)
        return backup_path

    def install_mod(self, mod_path: Path) -> None:
        """Instala un mod .zip en la carpeta de mods de Factorio.

        - Valida que sea un mod de Factorio válido.
        - Crea copia de seguridad si el mod ya existe.
        - No sobresale sin aviso.
        """
        mod_path = Path(mod_path)
        mods_folder = self._mods_folder()
        mods_folder.mkdir(parents=True, exist_ok=True)

        if not self.validate(mod_path):
            raise SecurityError(f"El archivo no es un mod de Factorio válido: {mod_path}")

        dest = mods_folder / mod_path.name
        if dest.exists():
            self._backup_file(dest)
            logger.info("Mod ya instalado, se creó copia de seguridad: %s", dest.name)

        shutil.copy2(mod_path, dest)
        logger.info("Mod instalado: %s -> %s", mod_path, dest)

    def uninstall_mod(self, mod_name: str) -> None:
        """Desinstala un mod de la carpeta de mods de Factorio.

        Crea una copia de seguridad antes de eliminar.
        """
        mods_folder = self._mods_folder()
        target = mods_folder / mod_name
        if not target.exists():
            raise SecurityError(f"El mod no está instalado: {mod_name}")

        self._backup_file(target)
        target.unlink()
        logger.info("Mod desinstalado: %s", target)

    def list_installed_mods(self) -> list[Path]:
        """Lista los mods instalados en la carpeta de mods de Factorio."""
        mods_folder = self._mods_folder()
        if not mods_folder.exists():
            return []
        return sorted(
            p for p in mods_folder.iterdir()
            if p.is_file() and p.suffix.lower() in self.supported_extensions
        )

    def get_installed_mod_metadata(self, mod_name: str) -> dict[str, Any] | None:
        """Lee los metadatos de un mod ya instalado."""
        mods_folder = self._mods_folder()
        target = mods_folder / mod_name
        return self.get_metadata(target)

    # ------------------------------------------------------------------
    # Detección de conflictos y dependencias
    # ------------------------------------------------------------------

    def check_dependencies(self, metadata: dict[str, Any]) -> list[str]:
        """Verifica si las dependencias del mod están instaladas.

        Devuelve una lista de nombres de dependencias faltantes.
        """
        installed = {
            p.name for p in self.list_installed_mods()
        }
        missing: list[str] = []
        for dep in metadata.get("dependencies", []):
            # Una dependencia puede venir como "nombre" o "nombre >= version"
            dep_name = dep.split(" ")[0].split(">=")[0].split("<=")[0].strip()
            # Buscar si existe un mod instalado con ese nombre (con o sin .zip)
            found = any(
                dep_name == name or dep_name == name.replace(".zip", "")
                for name in installed
            )
            if not found:
                missing.append(dep_name)
        return missing

    def detect_conflicts(
        self, new_mod_path: Path
    ) -> list[dict[str, str]]:
        """Detecta conflictos potenciales al instalar un nuevo mod.

        Conflictos detectados:
        - Mod ya instalado (mismo nombre de archivo).
        - Dependencias faltantes.
        - Versión de Factorio incompatible (si se puede determinar).

        Devuelve una lista de diccionarios con 'tipo' y 'mensaje'.
        """
        conflicts: list[dict[str, str]] = []
        mod_path = Path(new_mod_path)

        if not self.validate(mod_path):
            conflicts.append(
                {"tipo": "invalido", "mensaje": "El archivo no es un mod válido."}
            )
            return conflicts

        metadata = self.get_metadata(mod_path)
        if metadata is None:
            conflicts.append(
                {"tipo": "metadata", "mensaje": "No se pudieron leer los metadatos."}
            )
            return conflicts

        mods_folder = self._mods_folder()
        dest = mods_folder / mod_path.name
        if dest.exists():
            conflicts.append(
                {
                    "tipo": "duplicado",
                    "mensaje": f"El mod '{mod_path.name}' ya está instalado.",
                }
            )

        missing_deps = self.check_dependencies(metadata)
        for dep in missing_deps:
            conflicts.append(
                {
                    "tipo": "dependencia_faltante",
                    "mensaje": f"Dependencia faltante: {dep}",
                }
            )

        factorio_version = metadata.get("factorio_version", "")
        if factorio_version:
            conflicts.append(
                {
                    "tipo": "version_factorio",
                    "mensaje": f"Requiere Factorio {factorio_version}.",
                }
            )

        return conflicts
