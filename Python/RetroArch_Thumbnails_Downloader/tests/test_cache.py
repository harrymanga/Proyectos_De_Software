from core.cache import exists, get_cache_path, save


def test_cache_path_stable(tmp_path, monkeypatch):
    import core.cache as c
    monkeypatch.setattr(c, "CACHE_DIR", str(tmp_path))
    a = get_cache_path("https://x/y.png")
    b = get_cache_path("https://x/y.png")
    assert a == b
    assert a.endswith(".png")


def test_save_and_exists(tmp_path, monkeypatch):
    import core.cache as c
    monkeypatch.setattr(c, "CACHE_DIR", str(tmp_path))
    url = "https://x/game.png"
    assert exists(url) is False
    save(url, b"123")
    assert exists(url) is True


def test_save_guards():
    save(None, b"x")
    save("https://x", None)
    assert get_cache_path(None) is None
    assert exists(None) is False
