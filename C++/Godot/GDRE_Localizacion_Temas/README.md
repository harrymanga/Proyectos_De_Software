# GDRE Localización y Temas (overlay)

Overlay de español (+ futuros idiomas) y temas claro/oscuro para **Godot RE Tools v2.6.4**, sin modificar el árbol upstream.

- Upstream source original en: `/home/handerson/Descargas/Test/GDRE_Tools_v2.6.4` (ruta ya no válida en esta máquina)
- Copia local sibling disponible: `../GDRE_tools-v2.6.4-linux/` (binarios + `PCK/` exportado, útil como referencia de runtime, NO como árbol fuente `standalone/` para `extraer_cadenas.py`)
- Para re-extraer cadenas se requiere el árbol fuente (ej. `GDRETools/gdsdecomp @ v2.6.4` con `standalone/*.gd|*.tscn`); ver `UPSTREAM.md`
- Este proyecto solo contiene: plantillas de traducción, generador de tema claro, scripts de aplicación y documentación.
- Ver `UPSTREAM.md` (versión fijada) y `docs/ACTUALIZACIONES.md` (cómo re-aplicar tras actualizar GDRE).

## Estructura

```text
GDRE_Localizacion_Temas/
├── README.md
├── UPSTREAM.md
├── locale/
│   ├── README.md
│   └── es.csv            # plantilla (fuente en inglés, columna es por rellenar)
├── themes/
│   ├── README.md
│   └── generar_tema_claro.py
├── tools/
│   └── extraer_cadenas.py
├── scripts/
│   ├── aplicar_overlay.sh
│   └── verificar_actualizacion.sh
└── docs/
    └── ACTUALIZACIONES.md
```

## Uso rápido

```bash
# 1. Extraer cadenas UI del upstream a plantilla CSV (requiere árbol fuente con standalone/)
python3 tools/extraer_cadenas.py --upstream <RUTA_FUENTE_GDRETools-v2.6.4> --out locale/plantilla.csv

# 2. Generar tema claro a partir del tema oscuro upstream (fuente o PCK exportado)
python3 themes/generar_tema_claro.py --tema <RUTA_FUENTE>/standalone/gdre_theme.tres --out themes/gdre_theme_light.tres

# 3. Verificar qué cambió en una actualización upstream
bash scripts/verificar_actualizacion.sh --upstream /ruta/nueva/GDRE_Tools
```

## Requisitos

- Python 3 (solo stdlib) para las herramientas.
- Bash para los scripts. No se compila nada aquí.
