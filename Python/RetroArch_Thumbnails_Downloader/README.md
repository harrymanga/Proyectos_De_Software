# RetroArch Thumbnails Downloader v2.0

Descargador de thumbnails para RetroArch con interfaz gráfica, soporte multi-idioma, selección de coincidencias y renombrado de ROMs.

## 🌟 Características

- 🎮 **Detección automática de sistemas**: Reconoce múltiples consolas por extensión
- 🖼️ **Múltiples tipos de arte**: Boxarts, Snaps, Titles, Logos
- 📁 **Procesamiento por lotes**: Procesa múltiples carpetas y archivos simultáneamente
- 🔄 **Renombrado de ROMs**: Opcional, normaliza nombres de archivos
- 📊 **Interfaz gráfica intuitiva**: PyQt5 con barra de progreso y logs
- 🌍 **Soporte multi-idioma**: Español, English, Français con selección exclusiva
- 🎨 **Modo oscuro**: Tema claro/oscuro para mejor visualización
- 🔍 **Coincidencias exactas**: Diálogo simplificado con vista previa y selección de carpeta
- 🔎 **Búsqueda de alternativas**: Encuentra thumbnails similares cuando no hay coincidencia exacta
- 💾 **Selección de ruta personalizada**: Guarda thumbnails en cualquier ubicación
- ⚡ **Procesamiento paralelo**: Descargas concurrentes para mayor velocidad

## 📦 Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

### Interfaz Gráfica (Recomendado)

```bash
python main.py
```

### Funcionalidades de la Interfaz

1. **Añadir carpetas**: Click en "Añadir carpeta" para seleccionar directorios de ROMs
2. **Añadir archivos**: Click en "Añadir archivos ROM" para seleccionar archivos individuales
3. **Seleccionar sistema**: Elige el sistema de consola del combo (opcional, se detecta automáticamente)
4. **Tipo de arte**: Selecciona entre Named_Boxarts, Named_Snaps, Named_Titles o Named_Logos
5. **Renombrar ROMs**: Activa esta opción para normalizar nombres de archivos según el thumbnail
6. **Buscar coincidencias alternativas**: Activa para buscar thumbnails similares cuando no hay coincidencia exacta
7. **Iniciar proceso**: Click en "Iniciar" para comenzar la descarga
8. **Menú Tema**: Cambia entre modo claro y oscuro
9. **Menú Idioma**: Cambia entre Español, English y Français (solo un idioma activo a la vez)

### Coincidencias Exactas vs Alternativas

- **Coincidencia exacta**: Cuando se encuentra el thumbnail exacto, muestra un diálogo simplificado con:
  - Vista previa automática del thumbnail
  - Opción de seleccionar carpeta personalizada para guardar
  - Botones: Descargar, Omitir, Cancelar todo

- **Sin coincidencia exacta**: Cuando no se encuentra el thumbnail exacto y está activada "Buscar coincidencias alternativas":
  - Busca thumbnails similares
  - Muestra diálogo con lista de alternativas
  - Vista previa opcional de cada alternativa
  - Selección de carpeta personalizada

## 🔧 Build para Distribución

La aplicación puede ser compilada en ejecutables para Windows, Linux y macOS usando PyInstaller.

### Build Automático (Recomendado)

El script `build.py` detecta automáticamente el sistema operativo y compila la aplicación:

```bash
python build.py
```

### Build por Plataforma

#### Windows
```bash
build_windows.bat
```
El ejecutable se generará en `dist/windows/RetroArch Thumbnails Downloader.exe`

#### Linux
```bash
chmod +x build_linux.sh
./build_linux.sh
```
El ejecutable se generará en `dist/linux/RetroArch Thumbnails Downloader`

#### macOS
```bash
chmod +x build_macos.sh
./build_macos.sh
```
El application bundle se generará en `dist/macos/RetroArch Thumbnails Downloader.app`

### Build Manual con PyInstaller

Si prefieres usar PyInstaller directamente:

```bash
pyinstaller retro_thumbnails.spec --clean --noconfirm
```

## 🎮 Extensiones Soportadas

Los sistemas se configuran en `data/systems.json` con soporte para extensiones agrupadas:

- `.gba` - Nintendo - Game Boy Advance
- `.ciso, .gcm, .gcz, .iso, .nkit.gcz, .nkit.iso, .rvz` - Nintendo - GameCube
- `.n64, .v64, .z64` - Nintendo - Nintendo 64
- `.nes` - Nintendo - Nintendo Entertainment System
- `.nds` - Nintendo - Nintendo DS
- `.sfc, .smc` - Nintendo - Super Nintendo Entertainment System
- `.chd, .gdi` - Sega - Dreamcast
- `.bin, .cue` - Sony - PlayStation
- `.chd, .cso, .elf, .iso, .pbp, .prx` - Sony - PlayStation Portable
- `.chd, .iso` - Sony - PlayStation 2

## 📁 Estructura del Proyecto

```
retro_thumbnails/
├── main.py                      # Aplicación principal
├── requirements.txt             # Dependencias
├── retro_thumbnails.spec        # Configuración de PyInstaller
├── build.py                     # Script de build unificado
├── ui/                          # Componentes de interfaz
│   ├── frmMainWindow.ui        # Diseño Qt Designer
│   ├── frmMainWindow_ui.py     # Interfaz generada
│   └── match_dialog.py        # Diálogo de selección de coincidencias
├── build/                          # Scripts de build
│   ├── build_windows.bat        # Script de build para Windows
│   ├── build_linux.sh           # Script de build para Linux
│   └── build_macos.sh           # Script de build para macOS
├── core/                        # Lógica principal
│   ├── scanner.py              # Detección de sistemas
│   ├── matcher.py              # Normalización de nombres
│   ├── matcher_search.py       # Búsqueda de coincidencias alternativas
│   ├── downloader.py           # Descarga de imágenes
│   ├── cache.py                # Gestión de caché
│   └── worker_pool.py          # Procesamiento paralelo
├── data/                        # Configuración
│   └── systems.json            # Configuración de sistemas
└── locales/                     # Traducciones
    ├── es.json                 # Español
    ├── en.json                 # English
    └── fr.json                 # Français
```

## ⚙️ Configuración

### Sistemas

Los sistemas se configuran en `data/systems.json`. Las extensiones pueden agruparse separándolas por comas:

```json
{
  ".n64, .v64, .z64": "Nintendo - Nintendo 64",
  ".sfc, .smc": "Nintendo - Super Nintendo Entertainment System"
}
```

### Traducciones

Los archivos de traducción están en `locales/`:
- `es.json` - Español (por defecto)
- `en.json` - English
- `fr.json` - Français

Para agregar un nuevo idioma:
1. Crea un archivo `xx.json` en `locales/`
2. Copia el formato de `es.json`
3. Traduce todos los valores
4. Agrega la opción en el menú de idioma en `main.py`

## 🔬 Características Técnicas

- **Procesamiento paralelo**: Usa QThread para descargas simultáneas
- **Detección automática**: Detecta sistemas por extensión de archivo
- **Expansión de extensiones**: Soporta extensiones agrupadas en configuración
- **Manejo robusto de errores**: Captura y reporta errores específicos
- **Validación de entrada**: Verifica archivos y directorios antes de procesar
- **Logging detallado**: Muestra progreso y errores en tiempo real
- **Selección exclusiva de idiomas**: Solo un idioma activo en el menubar
- **Coincidencias exactas con diálogo**: Permite selección de carpeta personalizada
- **Vista previa de thumbnails**: Muestra imagen antes de descargar
- **Timeout en selección**: 30 segundos para selección del usuario

## 📚 Dependencias

- `PyQt5` - Interfaz gráfica
- `requests` - Descargas HTTP
- `pyinstaller` - Creación de ejecutables (solo para build)

## 📄 Licencia

Proyecto de código abierto para la comunidad de RetroArch.
