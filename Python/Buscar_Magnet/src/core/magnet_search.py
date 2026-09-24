"""Motor síncrono de búsqueda de magnets (sin GUI).

Uso como librería (ver workers.py) o CLI:
    python magnet_search.py URL [-d 2] [-u USER] [-p PASS] [-o output.json]
"""
import argparse
import json
import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def create_session(url, username=None, password=None, form_data=None):
    """Crea una sesión (con auth opcional). Lanza excepción si falla."""
    session = requests.Session()
    if username and password:
        session.auth = (username, password)
    elif form_data:
        response = session.post(url, data=form_data)
        response.raise_for_status()
    logger.info("Sesión iniciada correctamente.")
    return session


def extract_magnets_recursive(url, depth, visited, magnets, session):
    if depth == 0 or url in visited:
        return

    logger.debug("Visitando: %s", url)
    visited.add(url)

    try:
        response = session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (compatible; MagnetBot/1.0)'})
        response.raise_for_status()
        content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        for link in soup.find_all('a', href=True):
            if link['href'].startswith('magnet:'):
                strong_text = link.find('strong')
                key = strong_text.get_text(strip=True) if strong_text else "Enlace sin título"
                magnets[key] = link['href']

        for link in soup.find_all('a', href=True):
            target_url = urljoin(url, link['href'])
            if target_url.startswith(url) and urlparse(target_url).netloc == urlparse(url).netloc:
                extract_magnets_recursive(target_url, depth - 1, visited, magnets, session)

    except requests.exceptions.HTTPError as e:
        logger.warning("Error HTTP en %s: %s", url, e)
    except requests.exceptions.RequestException as e:
        logger.warning("Error de red en %s: %s", url, e)
    except Exception as e:
        logger.warning("Error al procesar %s: %s", url, e)


def save_json(magnets, output_path="data/magnets.json"):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(magnets, f, ensure_ascii=False, indent=4)
    logger.info("JSON creado: %s (%d enlaces)", output_path, len(magnets))


def search_magnets(url, depth, username=None, password=None, form_data=None,
           output="data/magnets.json"):
    """Búsqueda completa; devuelve dict y guarda JSON. Lanza ValueError si falla."""
    if not url:
        raise ValueError("URL vacía.")
    if not depth or depth <= 0:
        raise ValueError("Profundidad debe ser mayor a 0.")
    session = create_session(url, username, password, form_data)
    if session is None:
        raise ValueError("No se pudo iniciar sesión.")
    magnets = {}
    extract_magnets_recursive(url, depth, set(), magnets, session)
    save_json(magnets, output)
    return magnets


def main(argv=None):
    parser = argparse.ArgumentParser(description="Busca enlaces magnet (síncrono).")
    parser.add_argument("url")
    parser.add_argument("-d", "--depth", type=int, default=2)
    parser.add_argument("-u", "--user", default=None)
    parser.add_argument("-p", "--password", default=None)
    parser.add_argument("-o", "--out", default="data/magnets.json")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    enlaces = search_magnets(args.url, args.depth, args.user, args.password, output=args.out)
    print(f"Se encontraron {len(enlaces)} enlaces en {args.out}.")


if __name__ == "__main__":
    main()
