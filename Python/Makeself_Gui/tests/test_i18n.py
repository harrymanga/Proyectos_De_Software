"""Verifica paridad es/en: sin claves faltantes ni huérfanas."""
import json, os

LANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "lang")


def _load(code):
    with open(os.path.join(LANG_DIR, f"lang_{code}.json"), encoding="utf-8") as f:
        return json.load(f)


def test_idiomas_paridad():
    es, en = _load("es"), _load("en")
    assert set(es) == set(en), f"faltantes={set(es)^set(en)}"
    assert len(es) >= 20
    assert all(v.strip() for v in es.values())
