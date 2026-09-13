"""Jar Handler — operaciones JAR vía herramienta `jar` del JDK."""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

log = logging.getLogger("jartool")
TIMEOUT = 120


def _jar_bin() -> Optional[str]:
    return shutil.which("jar")


def _run(cmd: list[str], cwd: Path | str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None,
        capture_output=True, text=True, timeout=TIMEOUT,
    )


class JarHandler:
    """Extrae y crea JARs usando el comando `jar`."""

    def __init__(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir())

    def extract_jar(self, jar_path: str | Path, output_dir: str | Path | None = None) -> bool:
        jar = Path(str(jar_path))
        if not jar.is_file():
            log.error("JAR no existe: %s", jar)
            return False
        if _jar_bin() is None:
            log.error("Comando 'jar' no encontrado en PATH (instala un JDK)")
            return False
        out = Path(str(output_dir)) if output_dir else Path(f"{jar.stem}_extracted")
        try:
            out.mkdir(parents=True, exist_ok=True)
            r = _run(["jar", "xfv", str(jar)], cwd=out)
            if r.returncode != 0:
                log.error("Error al extraer %s: %s", jar, r.stderr.strip())
            return r.returncode == 0
        except subprocess.TimeoutExpired:
            log.error("Timeout extrayendo %s", jar)
            return False
        except OSError as e:
            log.error("Error OS extrayendo %s: %s", jar, e)
            return False

    def extract_multiple_jars(
        self, jar_paths: List[str | Path], base_output_dir: str | Path | None = None
    ) -> dict:
        results: dict = {}
        for jar_path in jar_paths:
            jar = Path(str(jar_path))
            if not jar.is_file():
                results[str(jar_path)] = False
                continue
            out = Path(str(base_output_dir)) / jar.stem if base_output_dir else Path(f"{jar.stem}_extracted")
            results[str(jar_path)] = self.extract_jar(jar, out)
        return results

    def create_jar(self, folder_path: str | Path, jar_path: str | Path | None = None) -> bool:
        folder = Path(str(folder_path))
        if not folder.is_dir():
            log.error("Carpeta no existe: %s", folder)
            return False
        if _jar_bin() is None:
            log.error("Comando 'jar' no encontrado en PATH (instala un JDK)")
            return False
        out_jar = Path(str(jar_path)) if jar_path else Path(f"{folder.name}.jar")
        try:
            out_jar.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mf", prefix="MANIFEST_",
                dir=str(self.temp_dir), delete=False, encoding="utf-8",
            ) as mf:
                mf.write("Manifest-Version: 1.0\nCreated-By: JarTool\n")
                manifest = mf.name
            try:
                r = _run(["jar", "cfm", str(out_jar), manifest, "-C", str(folder), "."])
            finally:
                Path(manifest).unlink(missing_ok=True)
            if r.returncode != 0:
                log.error("Error al crear %s: %s", out_jar, r.stderr.strip())
            return r.returncode == 0
        except subprocess.TimeoutExpired:
            log.error("Timeout creando %s", out_jar)
            return False
        except OSError as e:
            log.error("Error OS creando %s: %s", out_jar, e)
            return False

    def create_multiple_jars(
        self, folder_paths: List[str | Path], base_output_dir: str | Path | None = None
    ) -> dict:
        results: dict = {}
        for folder_path in folder_paths:
            folder = Path(str(folder_path))
            if not folder.is_dir():
                results[str(folder_path)] = False
                continue
            out = Path(str(base_output_dir)) / f"{folder.name}.jar" if base_output_dir else Path(f"{folder.name}.jar")
            results[str(folder_path)] = self.create_jar(folder, out)
        return results

    def get_jar_contents(self, jar_path: str | Path) -> List[str]:
        jar = Path(str(jar_path))
        if not jar.is_file():
            return []
        if _jar_bin() is None:
            log.error("Comando 'jar' no encontrado en PATH")
            return []
        try:
            r = _run(["jar", "tf", str(jar)])
            if r.returncode == 0:
                return [line for line in r.stdout.splitlines() if line]
            log.error("Error listando %s: %s", jar, r.stderr.strip())
            return []
        except (subprocess.TimeoutExpired, OSError) as e:
            log.error("Error listando %s: %s", jar, e)
            return []
