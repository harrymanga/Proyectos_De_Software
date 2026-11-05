"""Pruebas unitarias para FactorioValidator."""

from __future__ import annotations

from pathlib import Path

from src.core.factorio_validator import FactorioValidator


def test_validate_metadata_valid() -> None:
    validator = FactorioValidator()
    metadata = {
        "name": "TestMod",
        "version": "1.0.0",
        "author": "Autor",
        "factorio_version": "2.0",
    }
    errors = validator.validate_metadata(metadata)
    assert errors == []


def test_validate_metadata_missing_name() -> None:
    validator = FactorioValidator()
    metadata = {"version": "1.0.0"}
    errors = validator.validate_metadata(metadata)
    assert any("name" in e for e in errors)


def test_validate_metadata_missing_version() -> None:
    validator = FactorioValidator()
    metadata = {"name": "TestMod"}
    errors = validator.validate_metadata(metadata)
    assert any("version" in e for e in errors)


def test_validate_metadata_invalid_factorio_version() -> None:
    validator = FactorioValidator()
    metadata = {"name": "Test", "version": "1.0", "factorio_version": "99.0"}
    errors = validator.validate_metadata(metadata)
    assert any("factorio_version" in e.lower() or "versión" in e.lower() for e in errors)


def test_validate_metadata_invalid_version_format() -> None:
    validator = FactorioValidator()
    metadata = {"name": "Test", "version": "abc"}
    errors = validator.validate_metadata(metadata)
    assert any("versión" in e.lower() or "version" in e.lower() for e in errors)


def test_validate_metadata_forbidden_chars() -> None:
    validator = FactorioValidator()
    metadata = {"name": "Bad/Name", "version": "1.0"}
    errors = validator.validate_metadata(metadata)
    assert any("prohibido" in e or "caracteres" in e for e in errors)


def test_validate_zip_invalid_file(tmp_path: Path) -> None:
    validator = FactorioValidator()
    bad_zip = tmp_path / "not_a_zip.zip"
    bad_zip.write_text("esto no es un zip", encoding="utf-8")
    errors = validator.validate_zip(bad_zip)
    assert len(errors) > 0


def test_is_valid() -> None:
    validator = FactorioValidator()
    assert validator.is_valid({"name": "Test", "version": "1.0"}) is True
    assert validator.is_valid({"name": "", "version": "1.0"}) is False
