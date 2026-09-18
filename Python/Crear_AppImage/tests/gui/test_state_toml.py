"""La GUI debe heredar excluded_libraries del TOML (si no, linuxdeploy falla)."""

from pathlib import Path

from appimage_builder.gui.state import WizardState

TOML = """\
[tool.appimage-builder.project]
name = "Retro"
version = "2.0.1"
build_type = "python"
entry_point = "main:main"

[tool.appimage-builder.build]
excluded_libraries = ["libpq.so.5", "libQt53DAnimation.so.5"]
"""


def test_detect_preloads_excluded_libraries(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(TOML, encoding="utf-8")
    (tmp_path / "main.py").write_text("def main(): ...\n", encoding="utf-8")
    state = WizardState(project_path=tmp_path)
    state.detect()
    assert state.excluded_libraries == ["libpq.so.5", "libQt53DAnimation.so.5"]
    assert state.to_config().build.excluded_libraries == [
        "libpq.so.5",
        "libQt53DAnimation.so.5",
    ]


def test_detect_without_toml_keeps_defaults(tmp_path: Path) -> None:
    state = WizardState(project_path=tmp_path)
    state.detect()
    assert state.excluded_libraries == []
    assert state.to_config().build.excluded_libraries == []
