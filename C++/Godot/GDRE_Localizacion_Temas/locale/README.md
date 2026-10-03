# locale/

- `es.csv`: plantilla generada con `tools/extraer_cadenas.py` (columnas `clave,fuente_en,es`). Rellenar la columna `es`; no tocar `clave`.
- Nuevo idioma = copiar `es.csv` a `fr.csv`, `de.csv`… y traducir la última columna. Cero cambios de código en este overlay.
- Integración Godot (pendiente de implementar en el fork): cargar el CSV con `TranslationServer.add_translation()` al arrancar `gdre_main.gd`.
