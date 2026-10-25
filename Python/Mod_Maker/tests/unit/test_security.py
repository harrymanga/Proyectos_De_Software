"""Pruebas unitarias para el validador de seguridad."""

from __future__ import annotations

import pytest

from src.core.security import (
    SecurityError,
    is_dangerous_extension,
    is_path_within,
    validate_extraction_target,
    validate_mod_name,
)
from pathlib import Path


def test_is_path_within_returns_true_for_child() -> None:
    base = Path("/tmp/base")
    child = Path("/tmp/base/archivo.txt")
    assert is_path_within(base, child) is True


def test_is_path_within_returns_false_for_traversal() -> None:
    base = Path("/tmp/base")
    traversal = Path("/tmp/base/../../etc/passwd")
    assert is_path_within(base, traversal) is False


def test_validate_extraction_target_prevents_traversal(tmp_path: Path) -> None:
    """validate_extraction_target debe lanzar SecurityError ante traversal."""
    with pytest.raises(SecurityError):
        validate_extraction_target(tmp_path, "../../etc/passwd")


def test_is_dangerous_extension() -> None:
    assert is_dangerous_extension(Path("virus.exe")) is True
    assert is_dangerous_extension(Path("script.sh")) is True
    assert is_dangerous_extension(Path("datos.lua")) is False
    assert is_dangerous_extension(Path("info.json")) is False


def test_validate_mod_name_rejects_empty() -> None:
    with pytest.raises(SecurityError):
        validate_mod_name("")


def test_validate_mod_name_rejects_forbidden_chars() -> None:
    with pytest.raises(SecurityError):
        validate_mod_name("mod/name")


def test_validate_mod_name_accepts_valid() -> None:
    validate_mod_name("Mi_Mod_1.0")
