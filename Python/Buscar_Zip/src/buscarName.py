import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import os
import re

# URL inicial de la página web
url = 'https://winkawaks.org'

# Nombre del archivo JSON donde guardaremos los resultados
json_file = 'valores_name.json'

# Función para cargar datos previos del archivo JSON (si existe)
def load_existing_data():
    if os.path.exists(json_file):
        with open(json_file, 'r') as file:
            return json.load(file)
    return []

# Función para guardar los datos en el archivo JSON
def save_data_to_json(data):
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

# Función para extraer valores del atributo 'name' y realizar scraping recursivo
def extract_name_values(url, existing_data):
    # Hacer una solicitud GET a la página web
    response = requests.get(url)
    
    # Analizar el contenido HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Buscar todas las estructuras con "name = 'valor'"
    for tag in soup.find_all(attrs={"name": True}):
        # Obtener el valor de 'name' y añadirlo a la lista
        name_value = tag.get('name')
        if name_value and name_value not in existing_data:
            existing_data.append(name_value)
    
    # Ahora buscamos si hay enlaces a otras páginas para realizar la búsqueda recursiva
    # Si hay enlaces que contienen "next" o algún patrón que indique que hay más páginas, los seguimos
    for link in soup.find_all('a', href=True):
        # Suponiendo que el atributo 'href' contiene los enlaces a otras páginas para seguir buscando
        next_page = urljoin(url, link['href'])
        if next_page not in visited_urls:
            visited_urls.add(next_page)
            extract_name_values(next_page, existing_data)

# Cargar los datos existentes del archivo JSON (si hay)
existing_data = load_existing_data()

# Guardamos un conjunto de URLs visitadas para evitar visitas repetidas
visited_urls = set([url])

# Extraer los valores 'name' de la página inicial
extract_name_values(url, existing_data)

# Guardar los resultados en el archivo JSON
save_data_to_json(existing_data)

print(f"Se han guardado {len(existing_data)} valores 'name' en el archivo {json_file}.")
