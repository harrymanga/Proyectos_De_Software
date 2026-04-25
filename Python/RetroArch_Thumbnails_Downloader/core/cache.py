import os
import hashlib

CACHE_DIR = ".cache"

def get_cache_path(url):
    if not url:
        return None
    h = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, h + ".png")

def exists(url):
    cache_path = get_cache_path(url)
    return cache_path and os.path.exists(cache_path)

def save(url, content):
    if not url or not content:
        return
    
    cache_path = get_cache_path(url)
    if not cache_path:
        return
        
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(content)
