# Buscar_Zip

Scraping de ZIPs de ROMs en winkawaks.org.

## Contenido

- `src/main.py` — entrada principal (guarda `data/enlaces_zip.json`).
- `src/buscarName.py`, `src/busquedaRecursiva.py`, `src/generar_curl.py` —
  módulos de apoyo.
- `data/` — salida JSON.

## Uso (desde esta carpeta)

```bash
pip install requests beautifulsoup4
python src/main.py
```

## Pendiente

Consolidación con `Buscar_Magnet` y `WinKawaks_Roms_Download` (misma familia
descargadores) en una fase posterior.
