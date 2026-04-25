import requests
import os
import urllib.parse
from core.cache import exists, save, get_cache_path

def download(url, custom_path=None):
    if not url:
        return None
    
    # Si se proporciona una ruta personalizada, usarla
    if custom_path:
        # Verificar si ya existe en la ruta personalizada
        filename = os.path.basename(url).replace('.png', '')
        # Decodificar el nombre para que sea legible
        decoded_filename = urllib.parse.unquote(filename)
        custom_file = os.path.join(custom_path, f"{decoded_filename}.png")
        
        if os.path.exists(custom_file):
            return custom_file
        
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            
            if r.status_code == 200:
                # Crear directorio si no existe
                os.makedirs(custom_path, exist_ok=True)
                # Guardar en la ruta personalizada
                with open(custom_file, 'wb') as f:
                    f.write(r.content)
                return custom_file
            else:
                return None
        except requests.RequestException as e:
            print(f"Error descargando {url}: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado descargando {url}: {e}")
            return None
    
    # Usar el sistema de caché por defecto
    if exists(url):
        return get_cache_path(url)

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        
        if r.status_code == 200:
            save(url, r.content)
            return get_cache_path(url)
        else:
            return None
    except requests.RequestException as e:
        print(f"Error descargando {url}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado descargando {url}: {e}")
        return None
