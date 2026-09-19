# appimage-builder

![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Crea AppImages de forma automatizada, por CLI (Typer + Rich) o con un wizard
GUI de 7 pasos (PySide6 + MVVM). Soporta proyectos **Python**, **nativos**
(Rust, Go, CMake, Meson, Make) y **binarios precompilados** (incluido modo
árbol para apps portables con datos relativos).

## Instalación

```bash
pip install -e ".[dev,gui,build]"
```

O con los scripts por plataforma (ver `docs/usage.md`):

```bash
scripts/build-linux.sh
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

## Uso rápido

```bash
./run.sh --help   # crea .venv, instala el proyecto y muestra la ayuda
```

En Windows: `run.bat --help`. Equivalente manual (con el proyecto
instalado con `pip install -e .`):

```bash
# CLI
cd tu-proyecto
appimage-builder init                         # detecta y escribe [tool.appimage-builder]
appimage-builder build                        # dist/<nombre>-<arch>.AppImage
appimage-builder validate --appdir AppDir     # valida el resultado
appimage-builder doctor                       # diagnostica el entorno

# GUI
appimage-builder-gui [proyecto/]
```

Sin red, usa las herramientas vendorizadas en `tools/`:

```bash
appimage-builder build -p ./MiApp \
  --linuxdeploy ./tools/linuxdeploy-x86_64.AppImage \
  --appimagetool ./tools/appimagetool-x86_64.AppImage
```

Un AppImage puede exponer CLI y GUI a la vez (`--gui-entry-point`):

```bash
mi-app --version   # CLI
mi-app --gui       # GUI
```

## Documentación

- `docs/usage.md` — guía completa (comandos, configuración, hooks, GUI, troubleshooting)
- `docs/release.md` — versionado, CI y releases
- `tools/README.md` — herramientas offline vendorizadas
- `CHANGELOG.md` — cambios (detalle interno en `docs/interno/SESSION.md`)

## Desarrollo

```bash
python -m pytest tests/ -q            # 67 tests (marcadores: unit, integration, gui, slow)
python -m pytest tests/ -m "not slow" -q --cov --cov-report=term --cov-fail-under=60
ruff check src/ tests/ && ruff format --check src/ tests/
python -m mypy -p appimage_builder    # ratchet: bajar a 0 errores (ver CI typing)
tox                                   # matriz py311/py312 + lint
tox -e cov                            # coverage ratchet >=60%
tox -e typing                         # mypy
pre-commit install                    # hooks ruff + large-files
```

Estructura: `src/appimage_builder/` → `core/` (lógica compartida),
`cli/`, `gui/` (wizard MVVM), `builders/`, `bundler/`, `runtime/`,
`validators/`, `utils/`.

## Licencia

MIT — ver `LICENSE`.
