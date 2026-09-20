# Guía de uso — appimage-builder

Crea AppImages desde proyectos Python, nativos (Rust/Go/C/CMake/Meson/Make)
o binarios precompilados, por CLI o con el wizard GUI.

## Instalación

```bash
pip install -e ".[dev,gui,build]"
```

O con los scripts por plataforma (crean venv, instalan, generan `dist/`
y hacen smoke tests):

```bash
scripts/build-linux.sh                          # Linux (+ .desktop y AppImage opcionales)
VENV_DIR=/tmp/venv BUILD_DIST=0 scripts/build-linux.sh
INSTALL_DESKTOP=1 APPIMAGE=1 scripts/build-linux.sh
scripts/build-macos.sh                          # macOS (paquete local; AppImage es solo Linux)
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1   # Windows
scripts/build-appimage.sh                       # AppImage dual CLI+GUI (solo Linux; tools/ locales, red solo pip)
```

> En Python 3.14+ el extra `build` omite `pyside6-tools` (sin release para
> esa versión); el resto instala con normalidad.

Revisa el entorno con:

```bash
appimage-builder doctor
appimage-builder doctor --json   # salida para scripts
```

## Flujo rápido (CLI)

```bash
cd tu-proyecto
appimage-builder init            # detecta y escribe [tool.appimage-builder]
appimage-builder build           # construye dist/<nombre>-<arch>.AppImage
```

Overrides frecuentes (`CLI > ENV > TOML > defaults`):

```bash
appimage-builder build --name demo --version 1.0.0 \
  --entry-point demomod:main --build-type python --python-version 3.11 \
  --gui-entry-point demogui:main \
  --arch x86_64 --compression zstd --output dist/ --dry-run
```

Un AppImage con `gui_entry_point` expone ambos modos (`mi-app …` CLI,
`mi-app --gui` GUI; el `.desktop` abre la GUI).

Para proyectos con Qt u otras dependencias problemáticas en tu sistema,
excluye librerías del bundling de linuxdeploy (repetible):

```bash
appimage-builder build --exclude-library libpq.so.5 --exclude-library libodbc.so.2
```

Si el fallo es un árbol entero inútil (ej: `PyQt5/Qt5/qml` en apps solo-widgets,
cuyos plugins Qt3D/QML ni siquiera existen en los wheels de pip), pódalo del
AppDir **antes** de linuxdeploy (repetible, globs relativos al AppDir):

```bash
appimage-builder build --prune-path "usr/lib/python3*/site-packages/PyQt5/Qt5/qml"
```

```toml
[tool.appimage-builder]
build = { prune_paths = ["usr/lib/python3*/site-packages/PyQt5/Qt5/qml"] }
```

Apps portables precompiladas (carpeta con binarios + datos relativos, ej:
juegos): empaqueta el árbol completo y un shim en `usr/bin` que conserva
`$0` para los `cd` del lanzador:

```bash
appimage-builder build -p ./MiJuego --name mijuego --version 1.0 \
  --entry-point launcher.sh --build-type generic --bundle-tree --icon icon.png
```

El modo árbol excluye siempre `dist/`, `build/`, `__pycache__`,
`*.egg-info` y `*.AppImage` (un `dist/` dentro del proyecto nunca se
auto-empaqueta), y nunca pisa `AppRun` ni el `.desktop`/icono generados.

> Nota AppImage Python: el AppImage usa el `python3` del sistema anfitrión
> (≥3.11) más su payload en `usr/lib/python*/site-packages`. No incluye
> intérprete propio.

Variables de entorno: `APPIMAGE_BUILDER_PROJECT_NAME`,
`APPIMAGE_BUILDER_BUILD_OUTPUT`, `APPIMAGE_BUILDER_RUNTIME_CACHE_DIR`, etc.
Token para descargas de GitHub: `GITHUB_TOKEN`.

## Comandos

| Comando | Uso |
|---|---|
| `init [-p DIR] [--force] [--stdout] [--from-template N]` | Detecta y escribe la config inicial |
| `build [opts] [--dry-run]` | Construye el AppImage con progreso Rich |
| `validate [--appdir D] [--desktop F] [--metainfo F]` | Valida config/AppDir (exit 80 si falla) |
| `doctor [--json]` | Diagnóstico del entorno |
| `sign APPIMAGE [--key ID] [--output F.sig]` | Firma un AppImage con GPG |
| `template save/list/show/delete` | Plantillas en `~/.config/appimage-builder/templates/` |

## Configuración (`pyproject.toml`)

```toml
[tool.appimage-builder]
project = { name = "mi-app", version = "1.0.0", description = "...",
            build_type = "python", entry_point = "main:main", python_version = "3.11" }
build = { output = "dist", architecture = "x86_64", compression = "xz" }
runtime = { cache_dir = "~/.cache/appimage-builder" }
```

## Builds sin red

El repo vendoriza las herramientas en `tools/`. Úsalas así (también desde
la GUI en paso 5 → *Actualización y entorno*):

```bash
appimage-builder build -p ./MiApp \
  --linuxdeploy ./tools/linuxdeploy-x86_64.AppImage \
  --appimagetool ./tools/appimagetool-x86_64.AppImage
```

```toml
[tool.appimage-builder.runtime]
linuxdeploy_path = "tools/linuxdeploy-x86_64.AppImage"
appimagetool_path = "tools/appimagetool-x86_64.AppImage"
```

- `entry_point`: Python `modulo:funcion`; nativo/genérico nombre o ruta del binario.
- `gui_entry_point`: entry GUI opcional (mismo formato); habilita `--gui`.
- `update_information`: `gh-releases-<user>/<repo>` o `zsync|<url>` (opcional).
- `sign = true` + `sign_key` para firmar con GPG en el build.
- `bundle_tree = true` (genérico): empaqueta todo el árbol del proyecto.
- `excluded_libraries = ["libpq.so.5"]`: librerías que linuxdeploy debe saltar.

## Hooks

Scripts bash ejecutados con `APPDIR` en el entorno (`APPIMAGE` además en
post-install):

```toml
[tool.appimage-builder.build]
pre_package_hook = "scripts/pre.sh"
post_install_hook = "scripts/post.sh"
```

## GUI (wizard de 7 pasos)

```bash
appimage-builder-gui [proyecto/]
```

Bienvenida (detección + tema + ajustes) → Tipo → Específica → Metadatos
(icono arrastrable) → Avanzadas (árbol genérico, firma colapsable,
herramientas locales) → Build (Run/Cancel en
hilo, barras por etapa) → Finalización (abrir carpeta, copiar ruta, guardar
plantilla). Los ajustes (tema, cache, arch/compresión por defecto) persisten
en `QSettings`.

## Solución de problemas

- `No se pudo descargar`: revisa red, `GITHUB_TOKEN` y `~/.cache` escribible.
- `AppRun no es ejecutable` / `.desktop` inválido: `validate --appdir AppDir`.
- Sin FUSE: activa “Sin FUSE” (avanzadas) o `--appimage-extract`.
- `Firma GPG falló`: `gpg --list-secret-keys` y `--key` correcto.
- `entry_point inválido (Python)`: formato `modulo:funcion`.
