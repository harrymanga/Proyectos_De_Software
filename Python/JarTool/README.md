# JarTool - JAR File Manager

A modern PyQt6 application for extracting and compressing JAR files with support for multiple files, themes, and languages.

## Features

- **Multiple File Support**: Select and extract multiple JAR files simultaneously
- **Batch Compression**: Compress multiple folders into JAR files
- **Smart Naming**: Automatically creates folders with JAR file names during extraction
- **Theme Support**: Switch between light and dark themes
- **Multi-language**: Support for Spanish and English
- **Modular Architecture**: Clean separation of GUI, core logic, and tests

## Project Structure

```
JarTool1/
├── core/                   # Core functionality
│   ├── jar_handler.py     # JAR file operations using jar command
│   ├── theme_manager.py   # Theme management (light/dark)
│   ├── language_manager.py # Language management (es/en)
│   └── __init__.py
├── gui/                    # Graphical interface
│   ├── main_window.py     # Main application window
│   ├── ui_main_window.py  # UI components (generated)
│   └── __init__.py
├── main/                   # Application entry point
│   ├── main.py            # Main application launcher
│   └── __init__.py
├── test/                   # Test suite
│   ├── test_jar_handler.py
│   ├── test_theme_manager.py
│   ├── test_language_manager.py
│   └── __init__.py
├── mainwindow.ui          # Qt Designer UI file
├── requirements.txt       # Python dependencies
└── README.md              # This file
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
cd main
python main.py
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
- Click "Idioma" to toggle between Spanish and English

## Requirements

- Python 3.8+
- PyQt6
- Java Runtime Environment (for jar command)

## Testing

Run the test suite:

```bash
cd test
python -m unittest test_jar_handler.py
python -m unittest test_theme_manager.py
python -m unittest test_language_manager.py
```

Or run all tests:

```bash
cd test
python -m unittest discover
```

## Architecture

### Core Components

1. **JarHandler**: Manages JAR file operations using the system `jar` command
2. **ThemeManager**: Handles light/dark theme switching with CSS stylesheets
3. **LanguageManager**: Manages Spanish/English language switching

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

This project is open source and available under the MIT License.
