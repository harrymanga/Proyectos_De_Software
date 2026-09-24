import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import os

# URL de la página web inicial
start_url = 'https://freelinuxpcgames.com/'

# Nombre del archivo JSON donde guardaremos los enlaces
json_file = 'enlaces_zip1.json'

# Función para cargar datos previos del archivo JSON (si existe)
def load_existing_data():
    if os.path.exists(json_file):
        with open(json_file, 'r') as file:
            return json.load(file)
    return {}

# Función para guardar los datos en el archivo JSON
def save_data_to_json(data):
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

# Función recursiva para buscar archivos .zip en una página y en sus enlaces
def find_zip_links(url, visited, data):
    # Verificar si ya visitamos la URL
    if url in visited:
        return
    
    print(f"Visitando: {url}")
    visited.add(url)  # Marcar la URL como visitada

    try:
        # Hacer una solicitud GET a la página web
        response = requests.get(url)
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return

    # Analizar el contenido HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar enlaces en la página actual
    for tag in soup.find_all('a'):  # Buscar todas las etiquetas <a>
        link = tag.get('href')  # Obtener el atributo href (enlace)

        if not link:
            continue  # Ignorar enlaces vacíos

        # Convertir a enlace absoluto
        full_link = urljoin(url, link)

        # Verificar si el enlace es un archivo .zip
        if link.endswith('.zip'):
            # Obtener el nombre del archivo
            file_name = link.split('/')[-1]
            if file_name not in data:  # Solo agregar si es nuevo
                data[file_name] = full_link
                print(f"Encontrado archivo .zip: {file_name}")
        elif full_link.startswith(start_url):  # Continuar recursivamente dentro del dominio
            find_zip_links(full_link, visited, data)

# Cargar los datos existentes del archivo JSON (si hay)
existing_data = load_existing_data()

# Conjunto para rastrear las páginas ya visitadas
visited_urls = set()

# Buscar archivos .zip de forma recursiva desde la URL inicial
find_zip_links(start_url, visited_urls, existing_data)

# Guardar los resultados actualizados en el archivo JSON
save_data_to_json(existing_data)

print(f"Se han guardado {len(existing_data)} enlaces en el archivo {json_file}.")
