"""Motor asíncrono de búsqueda de magnets (sin GUI).

Uso como librería (ver workers.py) o CLI:
    python magnet_search_async.py URL [-d 2] [-o output.json]
"""
import argparse
import asyncio
import json
import logging
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Estado de la última búsqueda (ver workers.py: se reinicia por corrida).
magnets = {}
visited = set()


async def extract_magnets_recursive(session, url, depth):
    """Busca enlaces magnet de manera recursiva y concurrente."""
    if depth == 0 or url in visited:
        return

    logger.debug("Visitando: %s", url)
    visited.add(url)

    try:
        async with session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (compatible; MagnetBot/1.0)'}) as response:
            if response.status != 200:
                logger.warning("Error HTTP %s en %s", response.status, url)
                return

            content = await response.text()

            soup = BeautifulSoup(content, 'html.parser')

            for link in soup.find_all('a', href=True):
                if link['href'].startswith('magnet:'):
                    strong_text = link.find('strong')
                    key = strong_text.get_text(strip=True) if strong_text else "Enlace sin título"
                    magnets[key] = link['href']

            tasks = []
            for link in soup.find_all('a', href=True):
                target_url = urljoin(url, link['href'])
                if target_url.startswith(url) and urlparse(target_url).netloc == urlparse(url).netloc:
                    tasks.append(extract_magnets_recursive(session, target_url, depth - 1))

            await asyncio.gather(*tasks)

    except asyncio.TimeoutError:
        logger.warning("Tiempo de espera agotado en %s", url)
    except Exception as e:
        logger.warning("Error al procesar %s: %s", url, e)


async def start_async_search(url, depth):
    """Inicia la búsqueda recursiva asincrónica (acumula en globales)."""
    async with aiohttp.ClientSession() as session:
        await extract_magnets_recursive(session, url, depth)


def save_json(magnets, output_path="data/magnets.json"):
    """Guarda resultados en JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(magnets, f, ensure_ascii=False, indent=4)
    logger.info("JSON creado: %s (%d enlaces)", output_path, len(enlaces))


def search_async(url, depth, output=None):
    """Búsqueda completa asíncrona; devuelve dict. Lanza ValueError si falla."""
    if not url:
        raise ValueError("URL vacía.")
    if not depth or depth <= 0:
        raise ValueError("Profundidad debe ser mayor a 0.")
    global magnets, visited
    magnets = {}
    visited = set()
    asyncio.run(start_async_search(url, depth))
    resultado = dict(magnets)
    if output:
        save_json(resultado, output)
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(description="Busca enlaces magnet (asíncrono).")
    parser.add_argument("url")
    parser.add_argument("-d", "--depth", type=int, default=2)
    parser.add_argument("-o", "--out", default="data/magnets.json")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    magnets = search_async(args.url, args.depth, args.out)
    print(f"Se encontraron {len(magnets)} enlaces en {args.out}.")


if __name__ == "__main__":
    main()
