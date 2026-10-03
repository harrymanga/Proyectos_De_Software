# Proyectos de Software

Colección de proyectos de software desarrollados en diversos lenguajes y tecnologías.

## Proyectos Python

### JarTool
Herramienta GUI para empaquetar y desempaquetar archivos JAR.
- **Tecnologías**: PyQt6, PyInstaller
- **Características**: Multiplataforma, soporte de traducciones

### RetroArch Thumbnails Downloader
Descargador de miniaturas para RetroArch.
- **Tecnologías**: PyQt5, requests
- **Características**: Descarga automática, multi-sistema

### TraductorPro
Traductor multiplataforma de archivos (cfg/lang/txt/properties/json) con GUI Qt.
- **Tecnologías**: PyQt5, DeepL, OpenAI, googletrans
- **Características**: es/en + tema oscuro, placeholders, caché, 68 tests, icono AppImage-ready

### Buscar_Magnet / Buscar_Zip
Scraping de enlaces magnet y ZIPs de ROMs (pendiente de consolidación común).
- **Tecnologías**: requests, bs4, aiohttp, libtorrent

### CheatEngine_MCP_Bridge
Puente MCP para Cheat Engine (scripts `ce_bridge.sh`, `mcp_cheatengine_start.sh`, `ce_relay/tcp_relay`; ver su `AGENTS.md`/`CLAUDE.md`).

### Crear_AppImage
Herramienta automatizada CLI+GUI para crear AppImages (canónica; `run.sh`, `docs/`, `scripts/`).
- Ver `Python/Crear_AppImage/README.md`. Es la recomendada por `Crear_AppImage/Plantillas/`.

### Extraer_Strings_De_Archivos / Extraer_Texto
Extracción de textos traducibles desde código (pendiente de consolidación con Traducciones).

## Proyectos C++ / Godot

### GDRE_Localizacion_Temas
Overlay de español (+ futuros idiomas) y temas claro/oscuro para Godot RE Tools v2.6.4, sin modificar el upstream.
- **Ubicación**: `C++/Godot/GDRE_Localizacion_Temas/`
- **Upstream sibling**: `C++/Godot/GDRE_tools-v2.6.4-linux/` (binarios + `PCK/` exportado; la ruta fuente antigua ya no existe; ver `UPSTREAM.md`)
- **Características**: extractor de cadenas (182 UI), generador de tema claro, scripts de aplicación y verificación de actualizaciones

## Estructura

Cada proyecto incluye:
- Código fuente
- Documentación
- Scripts de compilación
- Archivos de configuración

## Requisitos

Ver los archivos `requirements.txt` en cada proyecto para las dependencias específicas.
