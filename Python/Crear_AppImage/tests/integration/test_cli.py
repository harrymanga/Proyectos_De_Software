"""Tests del CLI con Typer CliRunner."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from appimage_builder.cli.main import app

runner = CliRunner()


@pytest.mark.integration
def test_cli_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("build", "init", "validate", "doctor", "sign", "template"):
        assert command in result.output


@pytest.mark.integration
def test_cli_help_is_spanish() -> None:
    """Las opciones integradas de Typer/Click deben mostrar ayuda en español."""

    def plain(output: str) -> str:
        for box in "│─╭╮╰╯":
            output = output.replace(box, " ")
        return " ".join(output.split())  # Rich parte líneas y dibuja tablas

    for args in (["--help"], ["build", "--help"], ["doctor", "--help"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        text = plain(result.output)
        assert "Muestra esta ayuda y sale." in text
        assert "Show this message and exit." not in text
    root = plain(runner.invoke(app, ["--help"]).output)
    assert "Instala el autocompletado para el shell actual." in root
    assert "Install completion for the current shell." not in root


@pytest.mark.integration
def test_cli_version() -> None:
    from appimage_builder import __version__

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


@pytest.mark.integration
def test_doctor_json_is_valid() -> None:
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list) and payload
    assert all({"check", "status", "detail"} <= set(item) for item in payload)


@pytest.mark.integration
def test_init_stdout_detects_python(sample_python_project: Path) -> None:
    result = runner.invoke(app, ["init", "-p", str(sample_python_project), "--stdout"])
    assert result.exit_code == 0
    assert "python" in result.output


@pytest.mark.integration
def test_validate_config_only(sample_python_project: Path) -> None:
    result = runner.invoke(app, ["validate", "-p", str(sample_python_project)])
    assert result.exit_code == 0


@pytest.mark.integration
def test_validate_bad_appdir(tmp_path: Path, sample_python_project: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(
        app, ["validate", "-p", str(sample_python_project), "--appdir", str(empty)]
    )
    assert result.exit_code == 80


@pytest.mark.integration
def test_template_roundtrip(tmp_path: Path, isolated_home: Path) -> None:
    del isolated_home
    target = tmp_path / "proj"
    target.mkdir()
    (target / "pyproject.toml").write_text(
        '[tool.appimage-builder.project]\nname = "tpl"\nversion = "1.0.0"\n'
        'entry_point = "main:main"\n'
    )
    assert runner.invoke(app, ["template", "save", "demo", "-p", str(target)]).exit_code == 0
    listed = runner.invoke(app, ["template", "list"])
    assert listed.exit_code == 0 and "demo" in listed.output
    other = tmp_path / "other"
    other.mkdir()
    assert runner.invoke(app, ["init", "-p", str(other), "--from-template", "demo"]).exit_code == 0
    assert (other / "pyproject.toml").exists()
    assert runner.invoke(app, ["template", "delete", "demo"]).exit_code == 0
