from core.matcher import normalize, normalize_for_search


def test_normalize_basic():
    assert normalize("/roms/Super Mario World (USA).sfc") is not None
    assert "Super Mario World" in normalize("/roms/Super Mario World (USA).sfc").replace("%20", " ")


def test_normalize_strips_brackets_keeps_parens():
    out = normalize("Tetris [h1].nes")
    assert out is not None and "[" not in out


def test_normalize_empty():
    assert normalize("") is None
    assert normalize(None) is None
    assert normalize("   .nes") is None


def test_normalize_for_search():
    assert normalize_for_search("Super-Mario_World") == "supermarioworld"
