import os
import sys
import json

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta a un recurso, funciona tanto en desarrollo como en ejecutable PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En desarrollo, usar el directorio del script actual
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_systems():
    try:
        systems_path = get_resource_path('data/systems.json')
        with open(systems_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def expand_systems(systems):
    """Expande claves con múltiples extensiones separadas por comas en claves individuales."""
    expanded = {}
    for key, value in systems.items():
        # Si la clave contiene comas, separarla en extensiones individuales
        if ',' in key:
            extensions = [ext.strip() for ext in key.split(',')]
            for ext in extensions:
                expanded[ext] = value
        else:
            expanded[key] = value
    return expanded

def detect_system(file):
    if not file:
        return None
    
    ext = os.path.splitext(file)[1].lower()
    systems = load_systems()
    expanded_systems = expand_systems(systems)
    return expanded_systems.get(ext, None)

def validate_system_extension(file, system):
    """Valida que un archivo sea compatible con un sistema específico.
    
    Consulta el JSON original directamente para manejar correctamente
    extensiones compartidas entre múltiples sistemas (ej: .chd, .iso).
    
    Args:
        file: Ruta del archivo
        system: Nombre del sistema a validar (ej: "Nintendo - GameCube")
    
    Returns:
        True si la extensión del archivo es compatible con el sistema, False en caso contrario
    """
    if not file or not system:
        return False
    
    ext = os.path.splitext(file)[1].lower()
    systems = load_systems()
    
    # Consultar el JSON original: buscar si la extensión pertenece al grupo del sistema
    for key, value in systems.items():
        if value != system:
            continue
        # Separar las extensiones del grupo y comparar
        extensions = [e.strip() for e in key.split(',')]
        if ext in extensions:
            return True
    
    return False
