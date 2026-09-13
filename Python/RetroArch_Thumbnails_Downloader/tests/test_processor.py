from core.processor import build_thumbnail_url, find_rom_files, resolve_file


def test_build_url():
    assert build_thumbnail_url("S", "Named_Boxarts", "Game") == \
        "https://thumbnails.libretro.com/S/Named_Boxarts/Game.png"


def test_resolve_unknown():
    r = resolve_file("game.xyz123", "Named_Boxarts", None)
    assert r.status == "unknown_system"


def test_resolve_bad_extension():
    r = resolve_file("game.nes", "Named_Boxarts", "Sony - PlayStation 2")
    assert r.status == "bad_extension"


def test_resolve_ok():
    r = resolve_file("Super Mario World (USA).sfc", "Named_Boxarts", None)
    assert r.status == "ok"
    assert r.url.startswith("https://thumbnails.libretro.com/")


def test_find_rom_files_recursive(tmp_path):
    (tmp_path / "a.sfc").write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.nes").write_bytes(b"x")
    (tmp_path / "ignore.txt").write_bytes(b"x")
    found = find_rom_files(tmp_path, recursive=True)
    assert len(found) == 2
    flat = find_rom_files(tmp_path, recursive=False)
    assert len(flat) == 1
