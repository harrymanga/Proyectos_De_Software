import re
import json

def extraer_strings_y_variables(path_del_script):
    # Abrir el archivo para leer
    with open(path_del_script, 'r') as archivo:
        contenido = archivo.readlines()
    
    # Diccionario para almacenar los resultados
    resultados = {}
    
    # Expresión regular para encontrar asignaciones de strings a variables
    patron_asignacion = r'(\w+)\s*=\s*(["\'])(?:(?=(\\?))\2.)*?\1'
    # Expresión regular para encontrar strings en print
    patron_print = r'print\((["\'])(?:(?=(\\?))\1.)*?\1\)'
    
    for linea in contenido:
        # Buscar todas las coincidencias de asignaciones en la línea actual
        coincidencias_asignacion = re.findall(patron_asignacion, linea)
        for var, _, string in coincidencias_asignacion:
            resultados[var] = string
        
        # Buscar todas las coincidencias de prints en la línea actual
        coincidencias_print = re.findall(patron_print, linea)
        for string in coincidencias_print:
            # Usamos un identificador especial para los strings de print
            resultados[f"print_{linea.index(string)}"] = string

    # Crear el nombre del archivo JSON basado en el nombre del script
    nombre_archivo_json = path_del_script.split('/')[-1].replace('.py', '.json')
    
    # Guardar los resultados en un archivo JSON
    with open(nombre_archivo_json, 'w') as archivo_json:
        json.dump(resultados, archivo_json, indent=4)

    return nombre_archivo_json

# Ejemplo de uso (ruta relativa al proyecto; sobrescribible con APPIMAGE_BUILDER_* si se requiere absoluto)
if __name__ == "__main__":
    from pathlib import Path
    ruta_script = str(Path(__file__).resolve().parents[1] / "data" / "T1.P1.py")
    nombre_json = extraer_strings_y_variables(ruta_script)
    print(f"Los datos han sido guardados en {nombre_json}")