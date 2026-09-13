# JarTool - JAR File Manager

A modern PyQt6 application for extracting and compressing JAR files with support for multiple files, themes, and languages.

## Features

- **Multiple File Support**: Select and extract multiple JAR files simultaneously
- **Batch Compression**: Compress multiple folders into JAR files
- **Smart Naming**: Automatically creates folders with JAR file names during extraction
- **Theme Support**: Switch between light and dark themes
- **Multi-language**: es, en, fr, de, pt, ar (43 claves, RTL para árabe)
- **Modular Architecture**: Clean separation of GUI, core logic, and tests

## Project Structure

```
JarTool/
├── core/                   # Core functionality
│   ├── jar_handler.py     # JAR ops (shutil.which, timeout, logging, pathlib)
│   ├── theme_manager.py   # Theme management (light/dark)
│   ├── language_manager.py # Único manager (JSON-based, 6 idiomas)
│   └── __init__.py
├── gui/                    # Graphical interface
│   ├── main_window.py     # Main application window
│   ├── ui_main_window.py  # UI components
│   ├── worker_thread.py   # QThread sin sys.path hacks
│   └── language_selector.py
├── main/                   # Entry point
│   ├── main.py            # `python main/main.py` o `python -m main.main`
│   └── __init__.py
├── translations/           # es/en/fr/de/pt/ar.json (43 claves)
├── tools/
│   └── validate_translations.py  # Validador (ignora _metadata)
├── test/                   # pytest: jar_handler, theme, language, i18n_coverage
├── pyproject.toml          # ruff/mypy/pytest config
├── requirements-dev.txt
├── JarTool.spec            # portable (main/main.py, icons/jartool.ico)
├── build_all.py            # Orquestador (no bloquea CI con --yes/JARTOOL_ASSUME_YES=1)
├── build_linux.py / build_macos.py / build_windows.py
└── README.md
```

## Installation

1. Install Python 3.8 or higher
2. Install PyQt6:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main/main.py
# o
python -m main.main
```

### Features

#### Extract JAR Files
1. Select "Extraer archivo JAR" (Extract JAR file)
2. Click "Explorar" to select one or more JAR files
3. Optionally specify an output directory
4. Click "Ejecutar" to extract

#### Create JAR Files
1. Select "Crear archivo JAR desde carpeta" (Create JAR file from folder)
2. Click "Explorar" to select a folder
3. Optionally specify output JAR file location
4. Click "Ejecutar" to create JAR

#### Theme Switching
- Click "Temas" to toggle between light and dark themes

#### Language Switching
- es / en / fr / de / pt / ar (con soporte RTL)

## Requirements

- Python 3.9+
- PyQt6
- JDK con comando `jar` en PATH

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python tools/validate_translations.py
```

## Build (no interactivo en CI)

```bash
JARTOOL_ASSUME_YES=1 python build_all.py --no-tests
# o
python build_all.py --yes --no-tests
```

## AppImage (Linux)

Construido con `appimage_builder` (config en `[tool.appimage-builder]` de `pyproject.toml`):

```bash
appimage-builder build -p . \
  --linuxdeploy <appimage_builder>/tools/linuxdeploy-x86_64.AppImage \
  --appimagetool <appimage_builder>/tools/appimagetool-x86_64.AppImage
# → dist/JarTool-x86_64.AppImage (~260MB, incluye PyQt6)
```

Requiere Python 3.14 del sistema anfitrión y comando `jar` (JDK) en PATH en ejecución.

## Architecture

### Core Components

1. **JarHandler**: `jar` con `shutil.which`, `timeout=120s`, `logging`, `pathlib` + `NamedTemporaryFile`
2. **ThemeManager**: Handles light/dark theme switching with CSS stylesheets
3. **LanguageManager**: Único manager JSON-based (6 idiomas, fallback en→es, RTL)

### GUI Components

1. **JarToolWindow**: Main application window with all UI logic
2. **Ui_JarToolWindow**: Auto-generated UI components from Qt Designer

### Key Improvements

- **Uses jar command**: Properly handles JAR files without corruption
- **Multiple file selection**: Can process multiple files simultaneously
- **Modular design**: Clean separation of concerns
- **Comprehensive testing**: Unit tests for all core components
- **Theme support**: Professional light/dark themes
- **Internationalization**: Full Spanish/English support

## License

MIT — ver `LICENSE`.
