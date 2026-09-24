"""Lógica de búsqueda y verificación (sin GUI): emite eventos a una cola.

Eventos: ("found", dict) | ("verified", (ok, bad)) | ("progress", (i, n)) |
("error", str) | ("error_libtorrent", cmd) | ("done_search"|"done_verify", "").
"""
import threading

from core import magnet_search_async as async_mod
from core import magnet_search as sync_mod

_async_lock = threading.Lock()


def _install_cmd():
    """Comando de instalación de libtorrent según el gestor del sistema."""
    import shutil
    if shutil.which("pacman"):
        return "sudo pacman -S libtorrent-rasterbar"
    if shutil.which("apt-get") or shutil.which("apt"):
        return "sudo apt install python3-libtorrent"
    if shutil.which("dnf"):
        return "sudo dnf install python3-libtorrent"
    return "pip install libtorrent"


def _verifier():
    """Import perezoso: libtorrent es pesado/opcional hasta verificar."""
    try:
        from core import verify_magnet as verif_mod
        return verif_mod, ""
    except ImportError as e:
        return None, str(e)


def search_magnets(url, depth, engine, username, password, put):
    """Busca magnets (engine 'sync'|'async') y emite eventos."""
    try:
        enlaces = {}
        if engine == "async":
            with _async_lock:
                enlaces = async_mod.search_async(url, depth)
        else:
            import requests  # noqa: F401 (asegura dependencia temprana)
            session = sync_mod.create_session(url, username or None, password or None)
            sync_mod.extract_magnets_recursive(url, depth, set(), enlaces, session)
        put(("found", enlaces))
    except Exception as e:  # noqa: BLE001
        put(("error", str(e)))
    finally:
        put(("done_search", ""))


def verify_magnets(items, put):
    """Verifica semillas de [(clave, enlace)]. Progreso crudo (i, n)."""
    verif_mod, _err = _verifier()
    if verif_mod is None:
        put(("error_libtorrent", _install_cmd()))
        put(("done_verify", ""))
        return
    try:
        ok, bad = 0, []
        for i, (key, link) in enumerate(items, 1):
            put(("progress", (i, len(items))))
            try:
                if verif_mod.verify_magnet(link):
                    ok += 1
                else:
                    bad.append(key)
            except Exception as e:  # noqa: BLE001
                bad.append(f"{clave} ({e})")
        put(("verified", (ok, bad)))
    except Exception as e:  # noqa: BLE001
        put(("error", str(e)))
    finally:
        put(("done_verify", ""))
