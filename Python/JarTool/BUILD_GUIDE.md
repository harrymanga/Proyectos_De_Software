# 🚀 JarTool Build Guide

Guía completa para crear ejecutables de JarTool para Windows, Linux y macOS.

## 📋 Requisitos Previos

### Sistema
- Python 3.8 o superior
- Sistema operativo: Windows 10+, Ubuntu 18.04+, o macOS 10.13+
- Mínimo 2GB RAM libre para el proceso de build
- 500MB espacio en disco

### Dependencias Python
```bash
pip install -r requirements.txt
```

O instalar manualmente:
```bash
pip install PyQt6>=6.0.0 pyinstaller>=5.0
```

## 🎯 Opciones de Build

### Opción 1: Script Maestro (Recomendado)

```bash
# Build para plataforma actual
python build_all.py

# Build específico por plataforma
python build_all.py windows   # Solo Windows
python build_all.py linux     # Solo Linux
python build_all.py macos     # Solo macOS

# Opciones adicionales
python build_all.py --clean        # Limpiar builds anteriores
python build_all.py --no-tests     # Saltar tests
python build_all.py --skip-deps    # Saltar verificación de dependencias
```

### Opción 2: Scripts Individuales

```bash
# Windows
python build_windows.py

# Linux
python build_linux.py

# macOS
python build_macos.py
```

## 🪟 Build para Windows

### Requisitos Específicos
- Windows 10 o 11
- Python para Windows
- PyInstaller (se instala automáticamente)

### Proceso

```bash
# Desde Command Prompt o PowerShell
python build_windows.py
```

### Salida
```
dist/
├── JarTool_windows/
│   ├── JarTool.exe          # Ejecutable principal
│   ├── translations/         # Archivos de idioma
│   ├── README.txt           # Instrucciones
│   └── Start JarTool.bat    # Lanzador rápido
```

### Distribución
1. Comprimir carpeta `JarTool_windows/` como ZIP
2. Distribuir a usuarios Windows
3. Ejecutar `JarTool.exe` o `Start JarTool.bat`

## 🐧 Build para Linux

### Opción 1: AppImage (Recomendado)

#### Requisitos
```bash
# Instalar dependencias
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev

# Descargar appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

#### Build
```bash
python build_linux.py
```

#### Salida
```
dist/
├── JarTool-2.0.0-x86_64.AppImage    # AppImage portable
└── JarTool_linux.tar.gz              # Bundle alternativo
```

### Opción 2: Bundle Portable

```bash
tar -xzf JarTool_linux.tar.gz
cd JarTool_linux/
./run.sh
```

### Instalación AppImage
```bash
# Hacer ejecutable
chmod +x JarTool-*.AppImage

# Ejecutar
./JarTool-*.AppImage

# Instalar en sistema (opcional)
./JarTool-*.AppImage --appimage-extract
sudo mv squashfs-root /opt/JarTool
sudo ln -s /opt/JarTool/AppRun /usr/local/bin/jartool
```

## 🍎 Build para macOS

### Requisitos
- macOS 10.13 (High Sierra) o posterior
- Xcode Command Line Tools
```bash
xcode-select --install
```

### Proceso
```bash
python build_macos.py
```

### Salida
```
dist/
├── JarTool.app/                    # App Bundle
├── JarTool-2.0.0-macos.dmg         # Instalador DMG
└── JarTool-macos.zip               # Bundle ZIP
```

### Instalación
1. **DMG (Recomendado)**:
   - Abrir `JarTool-2.0.0-macos.dmg`
   - Arrastrar `JarTool.app` a Applications
   - Ejectuar desde Launchpad o Spotlight

2. **ZIP**:
   - Extraer `JarTool-macos.zip`
   - Mover `JarTool.app` a Applications

### Solución de Problemas macOS
```bash
# Si aparece "App can't be opened"
# Opción 1: Click derecho -> Open
# Opción 2: System Preferences -> Security -> Open Anyway

# Para quitar atributo de quarantine
xattr -cr /Applications/JarTool.app

# Verificar firma de código
codesign -dv --verbose=4 /Applications/JarTool.app
```

## 🔧 Build Manual Avanzado

### PyInstaller Directo

```bash
# Windows
pyinstaller --name=JarTool --windowed --onefile \
  --add-data=translations;translations \
  --hidden-import=PyQt6.sip \
  main/main.py

# Linux
pyinstaller --name=JarTool --windowed --onefile \
  --add-data=translations:translations \
  --hidden-import=PyQt6.sip \
  main/main.py

# macOS
pyinstaller --name=JarTool --windowed --onefile \
  --osx-bundle-identifier=com.jartool.app \
  --add-data=translations:translations \
  main/main.py
```

### Archivo Spec Personalizado

```bash
# Usar archivo spec para configuración avanzada
pyinstaller JarTool.spec
```

## 📦 Archivos Incluidos

### Estructura del Ejecutable

```
JarTool
├── JarTool(.exe|.app)
├── translations/
│   ├── es.json
│   ├── en.json
│   ├── fr.json
│   ├── de.json
│   ├── pt.json
│   └── ar.json
└── README.txt
```

### Módulos Incluidos
- ✅ PyQt6 (Qt6, Core, Gui, Widgets)
- ✅ Core: jar_handler, theme_manager, language_manager
- ✅ GUI: main_window, ui_main_window, worker_thread
- ✅ Traducciones: 6 idiomas

### Excluidos (para reducir tamaño)
- ❌ matplotlib
- ❌ numpy
- ❌ pandas
- ❌ scipy
- ❌ sklearn

## 🔍 Solución de Problemas

### PyInstaller No Encontrado
```bash
pip install pyinstaller
# o
python -m pip install pyinstaller
```

### Error: "translations not found"
```bash
# Asegurar que el directorio translations existe
ls translations/
# Debe contener: es.json, en.json, fr.json, de.json, pt.json, ar.json
```

### Error: "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### Windows: Error de Permisos
- Ejecutar Command Prompt como Administrador
- O usar PowerShell con políticas de ejecución:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux: appimagetool No Encontrado
```bash
# Descargar manualmente
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

### macOS: "Developer cannot be verified"
```bash
# Quitar atributo de quarantine
xattr -cr /Applications/JarTool.app
```

## 📊 Tamaños Esperados

| Plataforma | Formato | Tamaño Aproximado |
|------------|---------|-------------------|
| Windows    | .exe    | 45-55 MB          |
| Linux      | AppImage| 50-60 MB          |
| Linux      | tar.gz  | 45-55 MB          |
| macOS      | .app    | 50-60 MB          |
| macOS      | .dmg    | 55-65 MB          |

## 🌐 Cross-Compilación

### Limitaciones
- **Windows**: Requiere Windows nativo o VM/Wine
- **Linux**: Puede build en cualquier distro compatible
- **macOS**: **Requiere macOS nativo** (obligatorio por Xcode)

### Alternativa: GitHub Actions

Crear `.github/workflows/build.yml`:

```yaml
name: Build

on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build_windows.py
      - uses: actions/upload-artifact@v3
        with:
          name: JarTool-windows
          path: dist/JarTool_windows/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: sudo apt-get install -y python3-pyqt6
      - run: pip install pyinstaller
      - run: python build_linux.py
      - uses: actions/upload-artifact@v3
        with:
          name: JarTool-linux
          path: dist/*.AppImage

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build_macos.py
      - uses: actions/upload-artifact@v3
        with:
          name: JarTool-macos
          path: dist/*.dmg
```

## 📝 Notas de Versión

### v2.0.0
- ✅ Soporte multiplataforma (Windows, Linux, macOS)
- ✅ 6 idiomas: ES, EN, FR, DE, PT, AR
- ✅ AppImage para Linux
- ✅ DMG para macOS
- ✅ Instalador portable Windows
- ✅ Soporte RTL para árabe

## 🤝 Contribuir

Para agregar nuevos idiomas:
1. Crear `translations/xx.json`
2. Actualizar `core/language_manager.py` - `SUPPORTED_LANGUAGES`
3. Rebuild para todas las plataformas

## 📞 Soporte

Para problemas de build:
1. Revisar logs en `build/` directory
2. Verificar requisitos del sistema
3. Consultar solución de problemas arriba
4. Crear issue con logs completos

---

**Nota**: Los ejecutables son completamente standalone y no requieren instalación de Python o dependencias adicionales en la máquina destino.
