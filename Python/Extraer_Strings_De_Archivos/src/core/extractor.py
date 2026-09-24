import re
import ast
import json
import os


def leer_archivo(archivo_seleccionado):
    """Lee el contenido de un archivo y devuelve sus líneas."""
    with open(archivo_seleccionado, 'r', encoding='utf-8') as file:
        return file.readlines()


def procesar_lineas(lineas):
    """
    Extrae mensajes de string de las líneas de código Python.

    Busca:
    - Llamadas a print() con argumentos string
    - Llamadas a input() con prompts
    - Asignaciones de strings a variables
    - F-strings (cadenas con formato)
    """
    patron = re.compile(
        r'print\s*\(([^)]+)\)|'
        r'input\("([^"]+)"\)|'
        r'f"([^"]+)"|'
        r"f'([^']+)'"
    )
    patron_asig = re.compile(r"""^\s*([A-Za-z_]\w*)\s*=\s*(['"])(.+?)\2\s*$""")
    datos = {}
    for i, linea in enumerate(lineas):
        m_asig = patron_asig.match(linea)
        if m_asig is not None:
            # Asignación directa: conserva las comillas como el resto.
            datos[f"str_{m_asig.group(1)}"] = m_asig.group(2) + m_asig.group(3) + m_asig.group(2)
            continue
        matches = patron.findall(linea)
        for match in matches:
            mensaje = next(filter(None, match), None)
            if mensaje is None:
                continue
            if 'print' in linea:
                if 'f"' in linea:
                    mensaje = linea.split('"')[1].split('{')[0].strip()
                elif "f'" in linea:
                    mensaje = linea.split("'")[1].split('{')[0].strip()
                else:
                    mensaje = mensaje.split(',')[0].strip('\"')
                clave = f"str_print_line_{i+1}"
            else:
                variable_nombre = linea.split('=')[0].strip()
                clave = f"str_{variable_nombre}"
            datos[clave] = mensaje
    return datos


def extraer_strings_con_ast(archivo_seleccionado):
    """
    Extrae strings de un archivo Python usando el módulo ast.

    Este método es más robusto que las expresiones regulares, ya que
    analiza correctamente la sintaxis del código Python.

    Devuelve un diccionario con claves como 'str_print_line_N',
    'str_input_line_N' o 'str_<nombre_variable>'.
    """
    with open(archivo_seleccionado, 'r', encoding='utf-8') as file:
        contenido = file.read()

    tree = ast.parse(contenido)
    lineas = contenido.splitlines()
    datos = {}
    contador_print = {}
    contador_input = {}
    contador_assign = {}

    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Call):
            if isinstance(nodo.func, ast.Name):
                nombre_funcion = nodo.func.id
                if nombre_funcion == 'print' and nodo.args:
                    for arg in nodo.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            num_linea = nodo.lineno
                            contador_print[num_linea] = contador_print.get(num_linea, 0) + 1
                            indice = contador_print[num_linea]
                            clave = f"str_print_line_{num_linea}_{indice}"
                            datos[clave] = arg.value
                        elif isinstance(arg, ast.JoinedStr):
                            partes = []
                            for valor in arg.values:
                                if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
                                    partes.append(valor.value)
                            if partes:
                                num_linea = nodo.lineno
                                contador_print[num_linea] = contador_print.get(num_linea, 0) + 1
                                indice = contador_print[num_linea]
                                clave = f"str_print_line_{num_linea}_{indice}"
                                datos[clave] = ''.join(partes)
                elif nombre_funcion == 'input' and nodo.args:
                    for arg in nodo.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            num_linea = nodo.lineno
                            contador_input[num_linea] = contador_input.get(num_linea, 0) + 1
                            indice = contador_input[num_linea]
                            clave = f"str_input_line_{num_linea}_{indice}"
                            datos[clave] = arg.value

        elif isinstance(nodo, ast.Assign):
            for target in nodo.targets:
                if isinstance(target, ast.Name):
                    nombre_var = target.id
                    if isinstance(nodo.value, ast.Constant) and isinstance(nodo.value.value, str):
                        clave = f"str_{nombre_var}"
                        datos[clave] = nodo.value.value
                    elif isinstance(nodo.value, ast.JoinedStr):
                        partes = []
                        for valor in nodo.value.values:
                            if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
                                partes.append(valor.value)
                        if partes:
                            clave = f"str_{nombre_var}"
                            datos[clave] = ''.join(partes)

    return datos


def escribir_json(datos, nombre_json):
    """Escribe los datos extraídos en un archivo JSON."""
    with open(nombre_json, 'w', encoding='utf-8') as json_file:
        json.dump(datos, json_file, indent=4, ensure_ascii=False)
