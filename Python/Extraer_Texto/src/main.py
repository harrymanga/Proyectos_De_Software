import re
import json
import os

def extraer_textos(archivo):
    # Suponiendo que los textos están entre comillas
    with open(archivo, 'r', encoding='utf-8') as file:
        contenido = file.read()
    textos = re.findall(r'"([^"]*)"', contenido)
    return textos

def crear_json(textos, archivo_json):
    traducciones = {texto: "" for texto in textos}  # Crear un diccionario con textos vacíos
    with open(archivo_json, 'w', encoding='utf-8') as file:
        json.dump(traducciones, file, indent=4, ensure_ascii=False)

def reemplazar_textos(archivo, traducciones):
    with open(archivo, 'r', encoding='utf-8') as file:
        contenido = file.read()
    for original, traducido in traducciones.items():
        contenido = contenido.replace(f'"{original}"', f'"{traducido}"')
    with open(archivo, 'w', encoding='utf-8') as file:
        file.write(contenido)

# Uso de las funciones (rutas relativas a la raíz del proyecto).
# Ejecutar desde la raíz: python src/main.py
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
archivo_origen = os.path.join(BASE, "T1.P1.py")
archivo_json = os.path.join(BASE, "traducciones.json")
textos = extraer_textos(archivo_origen)
print(textos)  # Agrega esta línea para ver qué textos se están extrayendo
crear_json(textos, archivo_json)

# Supongamos que ya has editado el archivo JSON con las traducciones
#with open(archivo_json, 'r', encoding='utf-8') as file:
#    traducciones = json.load(file)
#print(traducciones)  # Para ver las traducciones cargadas

#reemplazar_textos(archivo_origen, traducciones)