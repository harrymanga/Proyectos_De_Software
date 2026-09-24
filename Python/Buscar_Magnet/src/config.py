"""Persistencia de preferencias en JSON del home."""
import json
import os

CONFIG = os.path.join(os.path.expanduser("~"), ".buscar_magnet.json")


def load_config(path=CONFIG):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(data, path=CONFIG):
    try:
        old = load_config(path)
        old.update(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(old, f)
    except OSError:
        pass


def save_json(path, data):
    """Escribe dict como JSON (I/O fuera de la GUI)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
