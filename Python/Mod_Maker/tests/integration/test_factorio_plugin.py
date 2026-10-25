"""Pruebas de integración para el plugin de Factorio.

Se crean archivos .zip temporales para validar extracción, reconstrucción,
instalación, desinstalación, metadatos, dependencias y conflictos
sin usar contenido con derechos de autor.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.plugins.factorio_group.factorio_plugin import FactorioPlugin


def _create_dummy_mod(
    tmp_path: Path,
    mod_name: str = "TestMod",
    version: str = "1.0.0",
    dependencies: list[str] | None = None,
    factorio_version: str = "1.1",
) -> Path:
    """Crea un .zip mínimo válido para Factorio en una carpeta temporal."""
    mod_dir = tmp_path / mod_name
    mod_dir.mkdir()
    info = {
        "name": mod_name,
        "version": version,
        "author": "Test",
        "description": "Mod de prueba",
        "factorio_version": factorio_version,
        "dependencies": dependencies or [],
    }
    (mod_dir / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    (mod_dir / "data.lua").write_text("-- datos de prueba\n", encoding="utf-8")
    zip_path = tmp_path / f"{mod_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(mod_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(mod_dir))
    return zip_path


def _create_mods_folder(tmp_path: Path) -> Path:
    """Crea una carpeta temporal para simular la carpeta de mods de Factorio."""
    mods_folder = tmp_path / "mods"
    mods_folder.mkdir()
    return mods_folder


def test_factorio_plugin_validate_accepts_valid_zip(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    zip_path = _create_dummy_mod(tmp_path)
    assert plugin.validate(zip_path) is True


def test_factorio_plugin_validate_rejects_missing_info_json(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    zip_path = tmp_path / "no_info.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.lua", "-- nada\n")
    assert plugin.validate(zip_path) is False


def test_factorio_plugin_validate_rejects_missing_required_fields(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mod_dir = tmp_path / "BadMod"
    mod_dir.mkdir()
    (mod_dir / "info.json").write_text(
        json.dumps({"name": "BadMod"}), encoding="utf-8"  # falta version
    )
    zip_path = tmp_path / "BadMod.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(mod_dir / "info.json", "info.json")
    assert plugin.validate(zip_path) is False


def test_factorio_plugin_get_metadata(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    zip_path = _create_dummy_mod(tmp_path, "MetaMod")
    metadata = plugin.get_metadata(zip_path)
    assert metadata is not None
    assert metadata["name"] == "MetaMod"
    assert metadata["version"] == "1.0.0"


def test_factorio_plugin_extract_and_build_roundtrip(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    zip_path = _create_dummy_mod(tmp_path, "RoundtripMod")
    extract_dir = tmp_path / "extracted"
    plugin.extract(zip_path, extract_dir)
    assert (extract_dir / "info.json").exists()
    assert (extract_dir / "data.lua").exists()

    rebuilt_zip = tmp_path / "rebuilt.zip"
    plugin.build(extract_dir, rebuilt_zip)
    assert rebuilt_zip.exists()
    assert plugin.validate(rebuilt_zip) is True


def test_factorio_plugin_install_and_uninstall(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)

    # Simular que la carpeta de mods es la temporal
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    zip_path = _create_dummy_mod(tmp_path, "InstallableMod")
    plugin.install_mod(zip_path)

    installed = plugin.list_installed_mods()
    assert any(p.name == "InstallableMod.zip" for p in installed)

    # Verificar copia de seguridad
    backups = list(mods_folder.glob("*.zip.bak"))
    assert len(backups) == 0  # primera instalación, no hay backup previo

    # Instalar de nuevo -> debe crear backup
    plugin.install_mod(zip_path)
    backups = list(mods_folder.glob("*.zip.bak"))
    assert len(backups) == 1

    # Desinstalar
    plugin.uninstall_mod("InstallableMod.zip")
    installed_after = plugin.list_installed_mods()
    assert not any(p.name == "InstallableMod.zip" for p in installed_after)

    # Debe existir backup después de desinstalar
    backups_after = list(mods_folder.glob("*.zip.bak"))
    assert len(backups_after) == 1  # el backup se reutiliza, no se acumulan infinitos


def test_factorio_plugin_check_dependencies(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    # Instalar un mod base
    base_zip = _create_dummy_mod(tmp_path, "BaseMod", version="1.0.0")
    plugin.install_mod(base_zip)

    # Crear un mod que depende de BaseMod
    dependent_zip = _create_dummy_mod(
        tmp_path, "DependentMod", dependencies=["BaseMod"]
    )
    metadata = plugin.get_metadata(dependent_zip)
    assert metadata is not None

    missing = plugin.check_dependencies(metadata)
    assert missing == []  # BaseMod está instalado

    # Crear un mod que depende de algo que no está instalado
    missing_dep_zip = _create_dummy_mod(
        tmp_path, "MissingDepMod", dependencies=["NoExisteMod"]
    )
    metadata_missing = plugin.get_metadata(missing_dep_zip)
    assert metadata_missing is not None
    missing = plugin.check_dependencies(metadata_missing)
    assert "NoExisteMod" in missing


def test_factorio_plugin_detect_conflicts_duplicate(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    zip_path = _create_dummy_mod(tmp_path, "ConflictMod")
    plugin.install_mod(zip_path)

    conflicts = plugin.detect_conflicts(zip_path)
    assert any(c["tipo"] == "duplicado" for c in conflicts)


def test_factorio_plugin_detect_conflicts_missing_dependency(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    zip_path = _create_dummy_mod(
        tmp_path, "NeedsDepMod", dependencies=["FaltanteMod"]
    )
    conflicts = plugin.detect_conflicts(zip_path)
    assert any(c["tipo"] == "dependencia_faltante" for c in conflicts)


def test_factorio_plugin_list_installed_mods_empty(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    mods = plugin.list_installed_mods()
    assert mods == []


def test_factorio_plugin_get_installed_mod_metadata(tmp_path: Path) -> None:
    plugin = FactorioPlugin()
    mods_folder = _create_mods_folder(tmp_path)
    plugin.get_mods_folder = lambda: str(mods_folder)  # type: ignore[method-assign]

    zip_path = _create_dummy_mod(tmp_path, "MetaInstalledMod")
    plugin.install_mod(zip_path)

    metadata = plugin.get_installed_mod_metadata("MetaInstalledMod.zip")
    assert metadata is not None
    assert metadata["name"] == "MetaInstalledMod"
