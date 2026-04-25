#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
from urllib.parse import quote

def search_matches(system, base_name, art_type="Named_Boxarts"):
    """
    Busca coincidencias en el servidor libretro para un nombre base de juego.
    
    Args:
        system: Nombre del sistema (ej: "Nintendo - Nintendo DS")
        base_name: Nombre base del juego (ej: "Tetris DS")
        art_type: Tipo de arte (Named_Boxarts, Named_Snaps, Named_Titles)
    
    Returns:
        Lista de tuplas (nombre, url) con las coincidencias encontradas
    """
    try:
        # Construir URL del directorio del sistema
        system_url = f"https://thumbnails.libretro.com/{quote(system, safe='')}/{art_type}/"
        
        # Obtener listado del directorio
        response = requests.get(system_url, timeout=10)
        if response.status_code != 200:
            return []
        
        # Extraer nombres de archivos del HTML
        html = response.text
        pattern = r'<a href="([^"]+\.png)">'
        matches = re.findall(pattern, html)
        
        # Filtrar coincidencias con el nombre base
        base_normalized = base_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        found_matches = []
        
        for match in matches:
            # Decodificar URL para comparar
            decoded_name = match.replace('.png', '').replace('%20', ' ').replace('%28', '(').replace('%29', ')')
            match_normalized = decoded_name.lower().replace(' ', '').replace('-', '').replace('_', '')
            
            # Buscar coincidencia parcial (el nombre base está contenido en el nombre del archivo)
            if base_normalized in match_normalized or match_normalized in base_normalized:
                full_url = f"{system_url}{match}"
                found_matches.append((decoded_name, full_url))
        
        return found_matches
        
    except Exception as e:
        print(f"Error buscando coincidencias: {e}")
        return []

def get_variants(base_name, system, art_type="Named_Boxarts"):
    """
    Genera variantes comunes de nombres para búsqueda.
    
    Args:
        base_name: Nombre base del juego
        system: Sistema del juego
        art_type: Tipo de arte
    
    Returns:
        Lista de URLs a probar
    """
    regions = ["(USA)", "(Europe)", "(Japan)", "(World)", "(USA, Europe)", "(En,Fr,De,Es,It)"]
    base_variants = []
    
    # Variante sin región
    base_variants.append(base_name)
    
    # Variantes con regiones comunes
    for region in regions:
        base_variants.append(f"{base_name} {region}")
    
    # Generar URLs
    urls = []
    for variant in base_variants:
        encoded_name = quote(variant, safe='')
        url = f"https://thumbnails.libretro.com/{quote(system, safe='')}/{art_type}/{encoded_name}.png"
        urls.append((variant, url))
    
    return urls
