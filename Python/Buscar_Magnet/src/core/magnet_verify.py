"""Verificación de semillas vía libtorrent (sin GUI).

Requiere el paquete del sistema (ej: pacman -S libtorrent-rasterbar).
Uso CLI: python verify_magnet.py input.json [-o output.json]
"""
import argparse
import json
import logging
import time

import libtorrent as lt

logger = logging.getLogger(__name__)


def verify_magnet(magnet_link):
    """True si el magnet tiene semillas activas."""
    session = lt.session()
    session.listen_on(6881, 6891)

    params = {
        'save_path': './',
        'storage_mode': lt.storage_mode_t(2)
    }
    handler = lt.add_magnet_uri(session, magnet_link, params)

    logger.debug("Conectando: %s", magnet_link)

    for _ in range(30):
        if handler.has_metadata():
            logger.debug("Metadatos obtenidos.")
            break
        time.sleep(1)
    else:
        logger.info("Sin metadatos: %s", magnet_link)
        return False

    for _ in range(15):
        state = handler.status()
        logger.debug("Seeders: %s, peers: %s", state.num_seeds, state.num_peers)
        if state.num_seeds > 0:
            logger.info("Con semillas: %s", magnet_link)
            return True
        time.sleep(1)

    logger.info("Sin semillas: %s", magnet_link)
    return False


def load_json(path):
    """Carga dict desde JSON. Lanza FileNotFoundError/ValueError si falla."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise ValueError(f"JSON vacío o inválido: {path}")
    return data


def save_json(data, filename="data/verification.json"):
    """Guarda resultados en JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info("Resultados guardados en: %s", filename)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verifica semillas de magnets.")
    parser.add_argument("input", help="JSON con {clave: magnet}")
    parser.add_argument("-o", "--out", default="data/verification.json")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    enlaces = load_json(args.input)
    results = {"Con semillas activas": [], "Sin semillas activas": []}
    for key, link in enlaces.items():
        (results["Con semillas activas"] if verify_magnet(link)
         else results["Sin semillas activas"]).append(link)
    save_json(results, args.out)
    print("Verificación finalizada.")


if __name__ == "__main__":
    main()
