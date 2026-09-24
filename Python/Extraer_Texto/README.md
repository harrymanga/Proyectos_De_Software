# Extraer_Texto

Extracción de textos traducibles desde scripts (regex por extensión) y
generación de JSON de traducciones.

## Contenido

- `src/main.py` — entrada (usa `data/T1.P1.py`, genera
  `data/traducciones.json`).
- `src/le.py`, `src/leer_Strings.py` — funciones de extracción.
- `data/` — muestra `T1.P1.py` + JSON.

## Uso (desde esta carpeta)

```bash
python src/main.py
```

Sin dependencias (stdlib). Rutas fijas `C:\...` corregidas a `data/`
relativo en esta reestructuración.

## Pendiente

Consolidación con `Extraer_Strings_De_Archivos` y el grupo B
(Traducciones) en una fase posterior.
