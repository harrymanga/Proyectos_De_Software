# Mod_Maker

Herramienta multiplataforma para crear, editar y gestionar mods de videojuegos. Incluye soporte inicial para **Factorio** (motor personalizado en C++ con Allegro para gráficos) y está diseñada para extenderse a otros juegos mediante plugins.

## Características

- Crear mods nuevos para juegos soportados (Factorio: archivos `.zip` con `info.json`).
- Extraer contenido de mods existentes a una carpeta de trabajo editable.
- Reconstruir (reempaquetar) mods extraídos y modificados.
- Gestor de mods por juego: listar, habilitar, deshabilitar y desinstalar mods.
- Sistema de plugins para agregar soporte a otros juegos (Unity, Unreal, Source, PAK genérico, etc.).
- Interfaz gráfica con temas claro y oscuro explícitos.
- Internacionalización: español e inglés (idiomas adicionales mediante archivos JSON).
- Multiplataforma: Windows, macOS y Linux.

## Requisitos

- Python 3.11 o superior.
- PySide6 (se instala automáticamente con el lanzador).

## Instalación y uso (arranque sin fricción)

### Linux / macOS

```bash
cd Mod_Maker
chmod +x run.sh
./run.sh
```

### Windows

```powershell
cd Mod_Maker
run.bat
```

El lanzador `run.sh` / `run.bat` crea el entorno virtual, instala las dependencias y ejecuta la aplicación (norma §56 del sistema de ingeniería de software).

## Distribución

Además del arranque con lanzador, se generan instaladores por sistema operativo:

- **Windows:** MSIX
- **macOS:** DMG
- **Linux:** AppImage / DEB

## Estructura del proyecto

```
Mod_Maker/
├── run.sh                 # Lanzador Linux/macOS
├── run.bat                # Lanzador Windows
├── requirements.txt       # Dependencias de Python
├── system-packages.txt    # Paquetes del sistema (si los hay)
├── pyproject.toml         # Configuración del proyecto
├── README.md              # Este archivo
├── CHANGELOG.md           # Registro de cambios
├── LICENSE
├── src/
│   ├── core/              # Lógica de negocio (config, mod, manager, extractor, builder, plugins, seguridad, i18n, logger)
│   ├── gui/               # Interfaz gráfica (ventana principal, temas, diálogos, widgets)
│   ├── lang/              # Traducciones (lang_es.json, lang_en.json, ...)
│   └── plugins/           # Plugins de juegos (factorio_group, unity_group, unreal_group, generic_pak)
├── data/                  # Plantillas y esquemas
├── tests/                 # Pruebas unitarias y de integración
├── docs/                  # Documentación (architecture, decisions/ADR, deployment, ...)
└── scripts/               # Scripts de utilidad
```

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install pytest ruff mypy

# Ejecutar pruebas
pytest

# Ejecutar lint
ruff check src/ tests/

# Ejecuttype checking
mypy src/
```

## Internacionalización

Los idiomas están en `src/lang/lang_xx.json`. Para agregar un nuevo idioma:

1. Copiar `src/lang/lang_es.json` a `src/lang/lang_xx.json` (donde `xx` es el código del idioma).
2. Traducir todas las claves.
3. No es necesario modificar código (carga dinámica, norma §57).

## Seguridad

- Se valida todo tipo de entrada del usuario (rutas, nombres de archivo, metadatos).
- Se previene path traversal al extraer archivos de mods.
- Se bloquean extensiones potencialmente peligrosas (`.exe`, `.dll`, `.sh`, etc.).
- Los mods no se ejecutan; solo se gestionan como archivos de datos.

## Licencia

MIT License. Consulte el archivo `LICENSE`.
