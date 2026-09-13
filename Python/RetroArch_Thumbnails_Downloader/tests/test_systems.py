from core.systems import (
    detect_system,
    expand_systems,
    list_extensions,
    validate_system_extension,
)


def test_expand_systems():
    out = expand_systems({".sfc, .smc": "SNES", ".nes": "NES"})
    assert out == {".sfc": "SNES", ".smc": "SNES", ".nes": "NES"}


def test_detect_system_case_insensitive():
    assert detect_system("game.SFC") == "Nintendo - Super Nintendo Entertainment System"
    assert detect_system("game.gba") == "Nintendo - Game Boy Advance"


def test_detect_unknown():
    assert detect_system("game.xyz123") is None
    assert detect_system("") is None
    assert detect_system(None) is None


def test_validate_shared_extension():
    assert validate_system_extension("x.iso", "Nintendo - GameCube") is True
    assert validate_system_extension("x.iso", "Sony - PlayStation 2") is True
    assert validate_system_extension("x.nes", "Sony - PlayStation 2") is False


def test_list_extensions_nonempty():
    assert ".nes" in list_extensions()
