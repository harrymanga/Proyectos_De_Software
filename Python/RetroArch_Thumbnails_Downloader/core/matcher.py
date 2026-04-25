import re
import os
import urllib.parse

def normalize(name):
    if not name:
        return None
    
    # Extraer solo el nombre del archivo sin extensión
    basename = os.path.basename(name)
    name_without_ext = os.path.splitext(basename)[0]
    
    if not name_without_ext:
        return None
    
    # Mantener mayúsculas/minúsculas originales para mejor coincidencia
    name = name_without_ext.strip()
    
    # Solo eliminar corchetes [ ] pero mantener paréntesis ( ) para regiones
    name = re.sub(r"\[.*?\]", "", name)
    
    # Limpiar solo caracteres problemáticos para URLs pero mantener símbolos importantes
    # Permitir: letras, números, espacios, (), -, _, #, .
    name = re.sub(r"[^a-zA-Z0-9\s\(\)\-\_\#\.]", " ", name)
    
    # Normalizar espacios múltiples
    name = re.sub(r"\s+", " ", name)
    
    result = name.strip()
    if not result:
        return None
    
    # Codificar para URL (manteniendo estructura original)
    return urllib.parse.quote(result, safe='')
