import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import os

# URL de la página web
url = 'https://winkawaks.org'

# Nombre del archivo JSON donde guardaremos los enlaces
json_file = 'data/enlaces_zip.json'

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

# Hacer una solicitud GET a la página web
response = requests.get(url)

# Analizar el contenido HTML con BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Cargar los datos existentes del archivo JSON (si hay)
existing_data = load_existing_data()

# Lista para almacenar los enlaces de archivos .zip (nuevos)
new_data = {}

# Buscar enlaces de archivos con extensión .zip
for tag in soup.find_all('a'):  # Buscar todas las etiquetas <a>
    link = tag.get('href')  # Obtener el atributo href (enlace)
    
    # Verificar si el enlace es un archivo .zip
    if link and link.endswith('.zip'):
        # Obtener el nombre del archivo (sin la URL base)
        file_name = link.split('/')[-1]  # Extrae el nombre del archivo
        full_link = urljoin(url, link)  # Convertir a enlace absoluto
        new_data[file_name] = full_link

# Agregar los nuevos resultados al diccionario existente
existing_data.update(new_data)

# Guardar los resultados actualizados en el archivo JSON
save_data_to_json(existing_data)

print(f"Se han guardado {len(new_data)} enlaces en el archivo {json_file}.")

