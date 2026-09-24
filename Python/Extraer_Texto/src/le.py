import re
import json

def extraer_strings_y_variables(path_del_script):
    # Determinar el lenguaje de programación por la extensión del archivo
    extension = path_del_script.split('.')[-1]
    
    # Diccionario para almacenar los resultados
    resultados = {}
 
    # Definir patrones de expresiones regulares para diferentes lenguajes
    if extension == 'py':
        # Python
        patron_asignacion = r'(\w+)\s*=\s*(["\'])(?:(?=(\\?))\2.)*?\1'
        patron_print = r'print\((["\'])(?:(?=(\\?))\1.)*?\1\)'
    elif extension == 'js':
        # JavaScript
        patron_asignacion = r'var\s+(\w+)\s*=\s*(["\'])(?:(?=(\\?))\2.)*?\1|let\s+(\w+)\s*=\s*(["\'])(?:(?=(\\?))\5.)*?\4|const\s+(\w+)\s*=\s*(["\'])(?:(?=(\\?))\8.)*?\7'
        patron_print = r'console\.log\((["\'])(?:(?=(\\?))\1.)*?\1\)'
    else:
        # Otros lenguajes o extensión desconocida
        return "Lenguaje no soportado o extensión desconocida"

    # Abrir el archivo para leer
    with open(path_del_script, 'r', encoding='utf-8') as archivo:
        contenido = archivo.readlines()
    
    for linea in contenido:
        # Buscar todas las coincidencias de asignaciones en la línea actual
        coincidencias_asignacion = re.findall(patron_asignacion, linea)
        for match in coincidencias_asignacion:
            var = match[0] or match[3] or match[6]  # Ajustar según los grupos de captura
            string = match[1] or match[4] or match[7]  # Ajustar según los grupos de captura
            resultados[var] = string
        
        # Buscar todas las coincidencias de prints en la línea actual
        coincidencias_print = re.findall(patron_print, linea)
        for string in coincidencias_print:
            resultados[f"print_{linea.index(string)}"] = string

    # Crear el nombre del archivo JSON basado en el nombre del script
    nombre_archivo_json = path_del_script.split('/')[-1].replace('.' + extension, '.json')
    
    # Guardar los resultados en un archivo JSON
    with open(nombre_archivo_json, 'w', encoding='utf-8') as archivo_json:
        json.dump(resultados, archivo_json, indent=4)

    return nombre_archivo_json

# Ejemplo de uso
ruta_script = 'C:\\Users\\Administrador\\Desktop\\T1.P1.py'  # Cambiar la extensión para probar con diferentes lenguajes
nombre_json = extraer_strings_y_variables(ruta_script)
print(f"Los datos han sido guardados en {nombre_json}")