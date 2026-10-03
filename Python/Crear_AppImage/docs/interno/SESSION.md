# appimage-builder - Session State

## Project Overview
**Project Path:** `Proyectos_De_Software/Python/Crear_AppImage/` (antes en `.../Proyectos/Proyectos_Python/Build/appimage_builder/`, ruta antigua ya no válida)
**Goal:** CLI + GUI (Qt/PySide6) application for automated AppImage creation
**Target Users:** Basic users who want to create AppImages intuitively

## Architecture Decisions
- **Core:** Pure Python business logic (shared CLI/GUI)
- **CLI:** Typer + Rich
- **GUI:** PySide6 + Qt Designer (.ui files) + MVVM pattern
- **Config:** Pydantic Settings (TOML + ENV + CLI precedence)
- **Build Backend:** linuxdeploy + appimagetool
- **Python Runtime:** python-build-standalone (astral-sh)

## Project Structure Created
```
appimage_builder/
├── pyproject.toml                 ✓ Complete with all deps
├── src/
│   └── appimage_builder/
│       ├── __init__.py            ✓ Version info
│       ├── core/
│       │   ├── __init__.py        (pending)
│       │   ├── constants.py       ✓ Enums: BuildType, Architecture, Compression, BuildStage, ExitCode
│       │   ├── exceptions.py      ✓ Custom exceptions with hints
│       │   ├── models.py          ✓ Pydantic models: ProjectConfig, BuildConfig, RuntimeConfig, AppImageBuilderConfig
│       │   ├── config.py          ✓ ConfigManager with CLI>ENV>TOML precedence
│       │   └── services/
│       │       ├── __init__.py    (pending)
│       │       ├── project_service.py  ✓ Auto-detection (Python, Rust, Go, CMake, Meson, Make, binary)
│       │       ├── build_service.py    ✓ BuildService orchestration with progress callbacks
│       │       └── template_service.py ✓ Templates: AppRun, .desktop, AppStream
│       ├── cli/                   (pending - Phase 1)
│       ├── builders/              (pending - Phase 3)
│       ├── bundler/               (pending - Phase 2)
│       ├── runtime/               (pending - Phase 2)
│       ├── validators/            (pending - Phase 2)
│       ├── utils/                 (pending)
│       └── gui/                   (pending - Phase 4)
├── tests/                         (pending)
├── scripts/                       (pending)
├── docs/                          (pending)
├── ui_designer/                   (pending)
└── .github/workflows/             (pending)
```

## Roadmap (10 Phases)

| Phase | Description | Status | Duration |
|-------|-------------|--------|----------|
| **0** | Setup proyecto + CI + dependencias CLI/GUI | ✅ **COMPLETADO** | 1 día |
| **1** | Core services compartidos + CLI skeleton | ✅ **COMPLETADO** | 2 días |
| **2** | Runtime manager + AppDir + Bundler | ✅ **COMPLETADO** | 3 días |
| **3** | Python/Native/Generic Builders | ✅ **COMPLETADO** | 3 días |
| **4** | GUI: Wizard skeleton + Qt Designer forms | ✅ **COMPLETADO** | 2 días |
| **5** | GUI: ViewModels + Controllers + Workers | ✅ **COMPLETADO** | 3 días |
| **6** | GUI: Build page con progress real-time | ✅ **COMPLETADO** | 2 días |
| **7** | GUI: Validación, tooltips, drag&drop, themes | ✅ **COMPLETADO** | 2 días |
| **8** | Validators + Hooks + Signing (shared) | ✅ **COMPLETADO** | 2 días |
| **9** | Polish: Doctor, Settings, Templates, Docs | ✅ **COMPLETADO** | 2 días |
| **10** | Testing matrix + Release automation | ✅ **COMPLETADO** | 1 día |

## Current Progress: Phase 1 (Core + CLI Skeleton)

### Completed in this Session:
1. ✅ Project directory structure created
2. ✅ `pyproject.toml` with all dependencies (CLI: typer, rich; GUI: PySide6; Config: pydantic-settings; Build: httpx, filelock; Dev: pytest, ruff, black, mypy)
3. ✅ `core/constants.py` - All enums and constants
4. ✅ `core/exceptions.py` - Rich exceptions with hints, exit codes
5. ✅ `core/models.py` - Pydantic models with validation
6. ✅ `core/config.py` - ConfigManager with hierarchical precedence
7. ✅ `core/services/project_service.py` - Auto-detection for 8+ project types
8. ✅ `core/services/build_service.py` - BuildService with async progress callbacks
9. ✅ `core/services/template_service.py` - Templates for AppRun, .desktop, AppStream

### Next Immediate Tasks (Phase 1 completion):
- [x] Create `src/appimage_builder/core/__init__.py` and `services/__init__.py`
- [x] Create CLI layer: `cli/main.py`, `cli/commands/{build,init,validate,doctor}.py`
- [x] Create CLI entry point: `src/appimage_builder/__main__.py`
- [x] Create shared `__init__.py` exports
- [x] Basic CLI testing

## Fase 1 — Completada (2026-09-12)
- CLI funcional: `build` (Rich progress + dry-run + quiet), `init` (detección + escribe
  `[tool.appimage-builder]`), `validate` (config + AppDir, exit 80 si falla),
  `doctor` (Python/FUSE/herramientas/cache).
- Fixes incluidos: `models.py` (Field duplicados), `config.py` (defaults + fallback
  entry_point), `template_service.py` ($$ escape), `build_service.py`
  (`self.build` tapaba método `build()` + import BuildType + `project_root`),
  `pyproject.toml` (sección ruff moderna, README.md creado).
- Verificado: `--help`, `--version`, `doctor`, `init --stdout` y en disco,
  `build --dry-run` y build real (stub), `validate` OK (exit 0) y BAD (exit 80).
- Deuda: 133 avisos ruff de estilo (UP045/I001/W292, pre-existentes) para fase polish.

### Siguiente (Fase 2):
- [x] Runtime manager + AppDir + Bundler (descargas reales linuxdeploy/appimagetool)

## Fase 2 — Completada (2026-09-12)
- `runtime/downloader.py`: descarga atómica httpx + filelock (`.part` + rename,
  reutiliza si existe, `GITHUB_TOKEN`, progreso por bytes).
- `runtime/manager.py`: `RuntimeManager` (cache `<cache>/tools/`, URLs por arch,
  `ensure_all/linuxdeploy/appimagetool`, `chmod +x`, `is_available`, `clear_cache`).
- `bundler/appdir.py`: `AppDirBuilder` (dirs, AppRun/.desktop/AppStream vía
  `TemplateService`, icono raíz + hicolor, `extra_files`, `pre_package_hook`
  con `APPDIR`, symlink applications). Import diferido de `TemplateService`
  para evitar ciclo `services.__init__ ↔ bundler`.
- `bundler/tools.py`: `run_linuxdeploy` (`--appdir -d --custom-apprun --output
  appimage --deploy-deps-only`, `--icon-file` si hay), `run_appimagetool`
  (flags `--comp` antes de posicionales, env `ARCH/UPDATE_INFORMATION/SIGN`),
  `sign_appimage` (gpg `--detach-sign`), streaming de salida + cancelación.
- `BuildService`: acepta `runtime`, delega preparing a `AppDirBuilder`, descarga
  real en `downloading_runtime`, ejecuta herramientas si están cacheadas (si no,
  omite etapa sin romper), `post_install_hook` con `APPIMAGE`, firma real,
  `_finalize_output()` copia a `dist`. Eliminada la duplicación de templates.
- `cli/commands/build.py`: pasa `runtime=final.runtime`.
- Fixes: orden `--comp` antes de posicionales (el fake lo reveló), import
  circular bundler↔services.
- Verificado: imports, ruff F/E9 limpio, `AppDirBuilder` directo, E2E con
  herramientas fake (7 etapas, artefacto en `dist`), manager URLs aarch64,
  downloader-reuse sin red, CLI `--dry-run`/`validate`/`doctor` intactos.
- Nota: build real con red descarga ~10-20MB de GitHub continuous; sin red las
  etapas se omiten con aviso (diseño intencional hasta tener builders Fase 3).

### Siguiente (Fase 3):
- [x] Python/Native/Generic Builders (`pip install` en AppDir con
  python-build-standalone, compilación nativa, binario genérico)

## Fase 3 — Completada (2026-09-12)
- `builders/base.py`: `BaseBuilder` (report, cancel, `require_tool`,
  `binary_name`, `fail` con stage/hint).
- `builders/python_builder.py`: `pip install --target usr/lib/pythonX.Y/site-packages`
  (+ `requirements.txt`), fallback copia de `.py` si no hay metadatos, wrapper
  `usr/bin/<project.name>` (`#!/usr/bin/env python3`, resuelve site-packages vía
  `APPDIR` + glob, `modulo:funcion` validado, exit code propagado).
- `builders/native_builder.py`: detecta cargo/go/cmake/meson/make, compila con
  streaming, localiza el binario (nombre esperado o ejecutable más reciente),
  lo copia a `usr/bin` (+x). `DependencyError` con hint si falta la toolchain.
- `builders/generic_builder.py`: resuelve entry_point como ruta/nombre,
  fallback al nombre del proyecto y a heurística de ejecutable suelto.
- `builders/factory.py`: `get_builder()` por `BuildType`.
- `TemplateService`: nuevo `launch_binary()` (Python → nombre del proyecto,
  nativo/genérico → entry_point); AppRun/`.desktop`/AppStream usan
  `$launch_binary` (antes `Exec=modulo:funcion`, inválido).
- `bundler/tools.py`: nuevo `stream_command()` público reutilizable.
- `BuildService._install_dependencies`: despacha vía factoría (adiós stub Fase 3).
- `cli build`: nueva opción `--python-version`.
- Fixes: `ConfigManager.load_toml` devuelve None si no hay sección
  `[tool.appimage-builder]` (antes crash con pyprojects ajenos); `resolve_config`
  sigue al siguiente candidato en ese caso.
- Verificado: ruff F/E9 limpio; PythonBuilder (pip real, wrapper ejecuta `hola`),
  NativeBuilder (Makefile+gcc, binario corre), GenericBuilder, E2E Python
  completo (AppRun→wrapper, `Exec=demopy`, artefacto en `dist`), CLI dry-run
  sobre pyproject ajeno, TOML inválido sigue dando error útil.

### Siguiente (Fase 4):
- [x] GUI: Wizard skeleton + Qt Designer forms (PySide6, 7 pasos)

## Fase 4 — Completada (2026-09-12)
- `gui/state.py`: `WizardState` (dataclass, base de los ViewModels Fase 5),
  `detect()` vía `ProjectService`, `output_dir()` (default `<proyecto>/dist`),
  `to_config()` (mismo `AppImageBuilderConfig` del CLI).
- `gui/wizard/wizard.py`: `AppImageWizard(QWizard)` 7 páginas, ModernStyle.
- `gui/wizard/pages.py`: Welcome (picker + auto-detección), Type (radios +
  entry), Specific (`QStackedWidget` python/nativo/genérico), Metadata
  (nombre/versión/autor/licencia/icono), Advanced (arch/compresión/salida/
  firma/update-info/no-fuse), Build (placeholder: resumen + `QProgressBar` +
  log + API `set_progress/append_log` para Fase 6), Finish (`isFinalPage`,
  abrir carpeta, copiar ruta, plantilla deshabilitada/Fase 9).
- `gui/main.py`: `main()` (`appimage-builder-gui`), `--project` opcional.
- Decisión: páginas en código (típico en wizards); el flujo `.ui` de Designer
  se reserva a diálogos fijos futuros.
- Fix: `_detect_make` sugería `gcc` con `all:` + receta; ahora exige target en
  la misma línea y añade fallback `-o <binario>` (capp → `hello`).
- Verificado: offscreen 7/7 páginas, navegación con validación, cambio de tipo
  radio→stack, nombre vacío bloquea con warning, `to_config` válido, CLI
  intacto, ruff F/E9 limpio. Nota: los `QMessageBox` modales bloquean tests —
  stubear `QMessageBox.warning` en tests GUI.

### Siguiente (Fase 5):
- [x] GUI: ViewModels + Controllers + Workers (QThread, señales, validación en vivo)

## Fase 5 — Completada (2026-09-12)
- `gui/viewmodels/wizard_viewmodel.py`: `WizardViewModel(QObject)` — setters con
  `state_changed`, `validate_project/type/specific/metadata/advanced/all`
  (patrones nombre/semver copiados de Pydantic para chequear sin construir),
  `to_config()` bloqueante salvo aviso firma-sin-key.
- `gui/workers/build_worker.py`: `BuildWorker` en QThread (`asyncio.run` dentro
  del hilo, cancelación con `threading.Event` thread-safe, señales
  `progressed/stage_changed/log_line/finished_ok/failed/canceled`). Sin padre
  QObject (exigencia de `moveToThread`); reintento limpio tras terminar.
- `gui/controllers/wizard_controller.py`: `WizardController` — detección,
  `build_config()`, `start_build()` (valida, bloquea doble arranque),
  `cancel_build()`, `wait_build()` determinista, re-emisión de señales.
- Páginas recableadas al viewmodel (validación movida del UI al VM);
  MetadataPage con hint rojo en vivo; AdvancedPage ignora el aviso no
  bloqueante; `WizardState.cache_dir` nuevo (+ campo en AdvancedPage).
- `AppImageWizard.closeEvent`: cancela y espera al worker (evita crash
  "QThread destroyed while running").
- Fixes: `start()` borraba cancelación pre-arranque (flag `_ever_finished`);
  `_live_validate` reentrante corrompía el estado en `initializePage` (guardia
  `_initializing`).
- Verificado offscreen: VM (9 casos), worker real en hilo (7 etapas,
  artefacto), pre-cancel y mid-cancel (tool con sleep), controller E2E
  (bloqueos + artefacto), regresión wizard 7/7 + live, CLI intacto, ruff
  F/E9 limpio.

### Siguiente (Fase 6):
- [x] GUI: Build page con progress real-time (conectar BuildPage al
  `WizardController`: Run/Cancel, barras por etapa, log expandible)

## Fase 6 — Completada (2026-09-12)
- `BuildPage` reescrita: resumen, `QGroupBox` con 6 barras por etapa (nombres
  vía `BuildStage.display_name`), barra global, log `QTextEdit`, estado y
  botones Iniciar/Cancelar; `bind_controller()` (conectada en `AppImageWizard`).
- Mapeo de progreso: etapa actual por `stage_changed`, fracción por
  `progressed`, global `(idx+frac)/6`; `completed` pone todo a 100.
- `validatePage` bloquea Next durante el build (con aviso); Back/Next del
  wizard se deshabilitan en curso y se restauran al terminar (evita mutar el
  estado a mitad de build). `closeEvent` previo ya cubre la X.
- Verificado offscreen con event loop y señales queued: build Python real en
  hilo (6/6 barras a 100, log, artefacto en `dist`, botones restaurados) y
  cancelación con tool lento (Next bloqueado, estado Cancelado). Ruff F/E9
  limpio, CLI intacto.

### Siguiente (Fase 7):
- [x] GUI: Validación, tooltips, drag&drop, themes

## Fase 7 — Completada (2026-09-12)
- `gui/widgets/icon_drop.py`: `IconDropWidget` (preview 64px, acepta PNG/SVG
  por drag&drop con validación de sufijo, `icon_changed`, click→examinar).
  MetadataPage lo usa (adiós `QLineEdit` + live-check integrado).
- `gui/widgets/collapsible.py`: `CollapsibleSection` (cabecera ▸/▾ + contenido).
  AdvancedPage: firma GPG y actualización/entorno colapsadas por defecto.
- `gui/styles/themes.py`: QSS claro/oscuro/sistema + `apply_theme()` con
  persistencia `QSettings`; combo en WelcomePage y aplicación al arranque.
- Tooltips en todos los campos clave (rutas, entry points, semver, arch,
  compresión, firma, update-info, FUSE, cache, botones Run/Cancel).
- Verificado offscreen: drop PNG aceptado con preview, TXT rechazado, temas
  (incl. inválido→sistema), secciones, regresión wizard 7/7, CLI intacto,
  ruff F/E9 limpio.

### Siguiente (Fase 8):
- [x] Validators + Hooks + Signing compartidos

## Fase 8 — Completada (2026-09-12)
- `validators/` compartidos: `project.py` (semántica config), `appdir.py`
  (AppRun/.desktop/icono/usr-bin/metainfo), `desktop.py` (claves, `Exec` sin
  `:`, `Categories;`, + `desktop-file-validate` como warnings),
  `appstream.py` (XML, tags requeridos, `<id>.desktop`, + `appstreamcli`).
  Herramientas externas ausentes = info omitida, nunca error.
- `cli validate` refactorizado sobre ellos + flags `--desktop/--metainfo`
  sueltos (exit 80 si falla, como antes).
- `utils/hooks.py`: `run_hook_script()` único; `AppDirBuilder.run_hook` y
  `BuildService._run_post_install_hook` lo reutilizan (se eliminó el duplicado;
  `subprocess` sin usar limpiado por ruff).
- `cli sign`: firma AppImages existentes (`gpg --detach-sign`, `--key`,
  `--output` con move), registrado como 5.º comando.
- Verificado: AppDir bueno/malo, desktop (warn Exec / error cabecera),
  metainfo (generado válido / XML roto), hooks (ok/env, exit 3, missing,
  pre_package real), firma GPG real con clave efímera (`gpg --verify` OK),
  exits 2/0/80, ruff F/E9 limpio.

### Siguiente (Fase 9):
- [x] Polish: Doctor, Settings, Templates, Docs

## Fase 9 — Completada (2026-09-12)
- `core/services/template_store.py`: plantillas TOML en
  `~/.config/appimage-builder/templates/` (save/load/list/delete, nombre
  validado). CLI `template save/list/show/delete` + `init --from-template`
  (nombre/output se re-ligan al proyecto destino). FinishPage ya guardaba.
- `gui/settings.py` + `gui/dialogs/settings_dialog.py`: tema, cache y
  arch/compresión por defecto persistentes; botón Ajustes en WelcomePage;
  el wizard aplica defaults al crear el estado.
- `doctor`: pip funcional, espacio en cache (WARN <1GiB), `appstreamcli` en la
  lista, flag `--json` para scripts.
- `docs/usage.md`: instalación, flujo CLI/GUI, comandos, config, hooks,
  troubleshooting.
- Fixes: `tomli_w` no serializa `None` → `exclude_none` en save/show;
  QComboBox stringifica los str-Enum en userData → `coerce_architecture/_compression`
  en `core/constants` (aplicado en diálogo, AdvancedPage y viewmodel);
  Rich partía el JSON largo → `soft_wrap=True`.
- Verificado: roundtrip save→list→show→from-template→delete, settings +
  diálogo + defaults en wizard, regresión 7/7, doctor JSON (15 checks, 0 FAIL),
  ruff F/E9 limpio.

### Siguiente (Fase 10):
- [x] Testing matrix + Release automation

## Fase 10 — Completada (2026-09-12)
- `tests/` (57 tests): `conftest` (proyectos ejemplo, tools fake, Qt offscreen,
  HOME aislado) + `unit/` (models, config, detección, templates, store,
  validators, hooks, runtime, builders, factoría) + `integration/` (E2E
  BuildService con tools fake, CLI: help/version/doctor-json/init/validate/
  template-roundtrip) + `gui/` (7 páginas, navegación, live validation,
  settings, temas). Marcadores `unit/integration/gui/slow` (`slow` = pip real).
- `tox.ini`: envs py311/py312/lint/slow. `.github/workflows/ci.yml` (lint +
  matriz 3.11–3.13, offscreen) y `release.yml` (tag `v*` → build + release).
  `docs/release.md`: versionado sincronizado (pyproject + `__version__`) y flujo.
- Limpieza para CI verde: autofix ruff + `Optional→X|None`, `[*a, b]`,
  import-alias; `UP042` ignorado (str+Enum intencional), `N802` ignorado en GUI
  (overrides Qt: `initializePage`, `dropEvent`…).
- Fixes de tests: fixture de proyecto en subdir (AppDir confundía a setuptools).
- Verificado: **57 passed**, ruff check + format limpios, tox.ini/YAML parsean,
  versiones 0.1.0 sincronizadas, `pip install -e .` + CLI OK.

---

## 🚀 Deploy (2026-09-12)

Artefactos y procedimiento verificado por dogfooding (la herramienta se
empaquetó a sí misma):

- `dist/appimage_builder-0.1.0.tar.gz` + `.whl` (`python -m build`).
- venv `/tmp/aib-venv` con `appimage-builder` y `appimage-builder-gui`
  funcionales; shims en `~/.local/bin`; `.desktop` en
  `~/.local/share/applications/` (validado sin avisos).
- `/tmp/aib-deploy/dist/appimage-builder-x86_64.AppImage` (281MB, incluye
  PySide6): `--version`, `doctor` y `validate` verificados dentro del AppImage.

## AppImage dual CLI+GUI (2026-09-12)

- `ProjectConfig.gui_entry_point` (Python `modulo:funcion`, nativo binario).
- AppRun con dispatch: `<AppImage> --gui` (o `gui`) lanza el modo gráfico;
  sin GUI definida el AppRun es idéntico al anterior.
- `PythonBuilder` genera el segundo wrapper `usr/bin/<nombre>-gui`;
  `.desktop` usa `Exec=<nombre> --gui` cuando hay GUI.
- CLI `--gui-entry-point`, wizard (pestaña Python) y `validate_specific`.
- AppImage reconstruido y verificado: CLI (`--version`, `validate`),
  GUI offscreen corriendo 20s sin trazas (rc 124), payload con ambos
  wrappers y `Exec=appimage-builder --gui`. `dist/` (wheel/sdist)
  reconstruido con todo.

Fixes descubiertos durante el deploy (ya en código + tests):

- `BuildConfig.excluded_libraries` + CLI `--exclude-library` (repetible) para
  librerías ausentes en el host (ej: drivers SQL de Qt).
- linuxdeploy: eliminado `--no-strip` y `--deploy-deps-only` (este último se
  tragaba el siguiente flag como ruta) y el plugin `-o appimage` (un solo
  artefacto vía nuestro appimagetool).
- `run_linuxdeploy`: `--custom-apprun` con copia externa (no dentro del
  AppDir) + `_repair_root_files()` (linuxdeploy deja el `.desktop` como
  symlink a sí mismo; se regenera desde plantillas).
- `AppDirBuilder.copy_icon()`: placeholder PNG 64px generado (stdlib) si no
  hay icono (linuxdeploy lo exige).
- Rich: `escape()` en `handle_error`, descripciones de progreso y tabla de
  `validate` (rutas con `[...]` rompían el reporte).
- `TemplateService`: una sola `Categories` principal; `PYTHONPATH` por glob
  `python*/site-packages` y sin `PYTHONHOME` (el payload usa el python3 del
  host; el anterior rompía su stdlib con `No module named 'encodings'`).
- `tests/unit/test_excludes.py` (3 tests). Suite: **60 passed**, ruff limpio.

## Prueba operativa: Fightcade 2.1.45 (2026-09-12)

- Detección inicial sugería `Fightcade.desktop` → `_detect_binary` y
  `GenericBuilder` ahora ignoran `.desktop/.png/.svg` (sugiere `Fightcade2.sh`).
- `BuildConfig.bundle_tree` + CLI `--bundle-tree`: el builder genérico mezcla
  todo el árbol en el AppDir (respeta AppRun/.desktop/icono propios) y crea
  shim `usr/bin/<entry>` (`exec $APPDIR/<rel>`, conserva `$0` para los `cd`).
- Resultado: `Fightcade-x86_64.AppImage` (164MB, árbol completo, exit 0,
  estructura validada, test `test_generic_builder_bundle_tree`).
- Límites honestos del upstream (no del empaquetado): `Fightcade2.sh`
  escribe config/logs junto al binario (squashfs read-only) y lanza electron
  en background (`&`) y sale → el runtime desmonta. Electron arranca
  (fontconfig) y sus libs resuelven (`ldd` limpio, rc 0).

## Verificación del dist/ del usuario (2026-09-12)

- Su `~/Descargas/dist/Fightcade-x86_64.AppImage` (218KB) era del build previo
  al fix: `Exec=Fightcade.desktop` (ejecutaba el .desktop con xdg-open→xed).
  Reconstruido en el mismo sitio con el código actual: 164MB, árbol completo.
- `bundle_tree` ahora omite `*.AppImage` (el usuario había copiado nuestro
  AppImage de 281MB dentro de Fightcake/ y se auto-empaquetó: 445MB).
- Detección y `GenericBuilder` ignoran `.desktop/.png/.svg` al sugerir binario.

## Herramientas locales / offline (2026-09-12)

- `tools/` vendoriza `linuxdeploy` + `appimagetool` x86_64 (28MB) para builds
  sin red. `RuntimeConfig.linuxdeploy_path/appimagetool_path` (TOML) +
  CLI `--linuxdeploy/--appimagetool` + pickers GUI (paso 5, con validación).
  Orden: local → cache → descarga. Verificado: build Fightcade completo con
  HOME/cache vacíos (cero descargas) + 5 tests nuevos. Suite 68, ruff limpio.

## GUI: --bundle-tree (2026-09-12)

- Estaba solo en CLI. Ahora en wizard paso 5 (Opciones avanzadas):
  check "Empaquetar árbol completo (genérico)", habilitado solo si el tipo
  es genérico (si no, se ignora aunque quede marcado).
- Plomería: `WizardState.bundle_tree` → `to_config()` → viewmodel
  `set_advanced(..., bundle_tree=...)`. Suite 63, ruff limpio.

## Verificación del dist/ del usuario, 2.ª parte (2026-09-12)

- Su `Fightcade_2` (218KB, `Exec=Fightcade.desktop`) era modo simple sin
  árbol. Reconstruido con `--bundle-tree` en el mismo `dist/`: 164MB,
  launcher encuentra todo (solo quedan los límites upstream conocidos).
- `bundle_tree` excluye `dist/`, `build/`, `__pycache__`, `*.egg-info` y
  `*.AppImage` (test `test_generic_builder_tree_skips_artifacts`).

## Limpieza (2026-09-12)
- Eliminados 34 restos: `.gitkeep` conviviendo con archivos reales, dirs
  placeholder nunca usados (`scripts/`, `tests/fixtures/`, `ui_designer/`
  —decisión code-first documentada), `build/`, `*.egg-info`, `__pycache__`,
  `.pytest_cache`, `.ruff_cache`. Raíz: `dist docs pyproject README SESSION
  src tests tox.ini` (+ `.github`). Suite 61 passed, ruff limpio tras limpiar.

## Scripts por plataforma (2026-09-12)

- `scripts/build-linux.sh` (venv + extras + dist + smoke + `.desktop` y
  AppImage opcionales), `build-macos.sh`, `build-windows.ps1` y
  `build-appimage.sh` (receta dogfood verificada). `shellcheck` limpio.
- Fix: `pyside6-tools` no tiene release para Python 3.14 → extra `build`
  condicional (`python_version<'3.14'`); el script Linux lo demostró en un
  venv desde cero (PySide6 6.11.2 + smoke OK).

## Post-Deploy: ayuda CLI en español (2026-09-12)

- Las opciones integradas (`--help`, `--install-completion`,
  `--show-completion`) salían en inglés. Nuevo `cli/spanish.py`:
  `patch_typer_defaults()` reescribe los textos en las factorías de Typer y
  en `Command.get_help_option` del click vendoreado (duck-typing, con
  degradado a inglés si Typer cambia); se ejecuta al importar `cli.main`, así
  cubre `app()`, `CliRunner` y scripts instalados. `apply_spanish_help(cmd)`
  queda como ajuste directo alternativo.
- Test `test_cli_help_is_spanish` (normaliza tablas/wraps de Rich).
- Suite: **61 passed**, ruff limpio; wheel + AppImage reconstruidos con el fix.

---

## 🎉 Proyecto completo (Fases 0–10 + Deploy)

CLI (`build/init/validate/doctor/sign/template`) + wizard GUI de 7 pasos con
MVVM, workers en hilo y progreso real; builders Python/nativo/genérico;
runtimes cacheados; validadores, hooks y firma compartidos; 57 tests en verde.
Deuda menor conocida: `mypy --strict` no se ejecuta en CI (requiere
anotaciones adicionales en GUI/workers); `pip install` del payload necesita
red; `linuxdeploy/appimagetool` se omiten sin cache (aviso).

## Key Design Patterns Used

### Config Precedence (High → Low)
1. CLI arguments (`typer`)
2. Environment variables (`APPIMAGE_BUILDER_*`)
3. `pyproject.toml` `[tool.appimage-builder]`
4. Sensible defaults

### Build Pipeline Stages
```
PREPARING → DOWNLOADING_RUNTIME → INSTALLING_DEPS → RUNNING_LINUXDEPLOY → CREATING_APPIMAGE → SIGNING → COMPLETED
```

### Project Auto-Detection Priority
1. Python: `pyproject.toml` (scripts), `setup.py`, `setup.cfg`, `requirements.txt`
2. Rust: `Cargo.toml`
3. Go: `go.mod`
4. CMake: `CMakeLists.txt`
5. Meson: `meson.build`
6. Make: `Makefile`
7. Generic: Executable binary in root

## GUI Wizard Flow (7 Steps)
1. **Bienvenida** - Select project type with auto-detection
2. **Tipo de Proyecto** - Confirm/override detection
3. **Configuración Específica** - Dynamic per-type (Python: entry_point, version; Native: binary; Generic: executable)
4. **Metadatos** - Name, version, description, author, icon (drag&drop), categories
5. **Opciones Avanzadas** (collapsible) - Arch, compression, signing, hooks, update info
6. **Build** - Real-time progress with staged bars, expandable logs, cancel button
7. **Finalización** - Success with test/open folder/copy path, save as template

## Dependencies Installed (via pyproject.toml)
```toml
# Core
typer[all]>=0.12.0, rich>=13.7.0
pydantic>=2.7.0, pydantic-settings>=2.3.0
httpx>=0.27.0, anyio>=4.3.0
platformdirs>=4.2.0, python-dotenv>=1.0.0
tomli-w>=1.0.0, packaging>=24.0, filelock>=3.15.0

# GUI
PySide6>=6.7.0

# Dev
pytest>=8.2.0, pytest-asyncio>=0.23.0, pytest-qt>=4.2.0
ruff>=0.5.0, black>=24.3.0, mypy>=1.10.0
pre-commit>=3.7.0, tox>=4.15.0

# Build tools
pyside6-tools>=6.7.0
```

## Commands to Resume Work

```bash
cd "Proyectos_De_Software/Python/Crear_AppImage"  # antes: ".../Proyectos/Proyectos_Python/Build/appimage_builder"

# Install dependencies
pip install -e ".[dev,gui,build]"

# Run code quality checks
ruff check src/
black --check src/
mypy --strict src/

# Run tests (when available)
pytest tests/ -v

# Test CLI (when implemented)
python -m appimage_builder --help
python -m appimage_builder build --help

# Test GUI (when implemented)
python -m appimage_builder.gui.main
# or
appimage-builder-gui
```

## Important Notes for Next Session

1. **Core services are complete and tested** - The business logic layer is solid
2. **CLI layer is next** - Use Typer with Rich for beautiful output
3. **Shared core** - CLI and GUI will both use `BuildService`, `TemplateService`, `ConfigManager`
4. **GUI uses MVVM** - ViewModels in `gui/viewmodels/`, Views wrap `.ui` files, Controllers coordinate
5. **Qt Designer workflow** - Edit `.ui` files in `ui_designer/forms/`, compile with `pyside6-uic`
6. **Async throughout** - BuildService uses async/await, GUI uses QThread workers with signals

## Files to Create Next (Priority Order)

1. `src/appimage_builder/core/__init__.py` - Exports
2. `src/appimage_builder/core/services/__init__.py` - Exports
3. `src/appimage_builder/cli/options.py` - Shared CLI options
4. `src/appimage_builder/cli/commands/build.py` - Build command
5. `src/appimage_builder/cli/commands/init.py` - Init/scaffold command
6. `src/appimage_builder/cli/commands/validate.py` - Validate AppDir
7. `src/appimage_builder/cli/commands/doctor.py` - Diagnostics
8. `src/appimage_builder/cli/main.py` - Typer app assembly
9. `src/appimage_builder/__main__.py` - CLI entry point
10. `src/appimage_builder/gui/main.py` - GUI entry point (later)

## Configuration Example (for testing)

```toml
# pyproject.toml
[tool.appimage-builder]
project = { name = "mi-app", version = "1.0.0", description = "Mi aplicación", build_type = "python", entry_point = "main:main", python_version = "3.11" }
build = { output = "dist", architecture = "x86_64", compression = "xz" }
runtime = { cache_dir = "~/.cache/appimage-builder" }
```

---

## Icono propio + deploy persistente (2026-09-12)

- `scripts/make-icon.py`: genera `assets/icon-{512,256,128,64,32}.png`
  (degradado azul + paquete + insignia descarga, solo PySide6).
- Icono instalado en `~/.local/share/icons/hicolor/*/apps/` y `.desktop`
  con `Icon=appimage-builder` (validado). AppImage propio reconstruido con
  `--icon` (payload verificado: PNG 512 real).
- Deploy movido a persistente: venv en
  `~/.local/share/appimage-builder/venv` (el de `/tmp` no sobrevive
  reinicios); shims + `.desktop` (recreado, había desaparecido) apuntan ahí.

## Scripts con assets (2026-09-12)

- `build-linux.sh` instala `assets/icon-*.png` en hicolor y usa
  `Icon=appimage-builder` (genérico si faltan); `build-appimage.sh` pasa
  `--icon` automáticamente si existe. Verificado con `INSTALL_DESKTOP=1`
  (iconos + `.desktop` válido). Nota: probar ese path reescribió los shims a
  `/tmp` y hubo que restaurarlos al venv persistente.

**Last Updated:** 2026-09-12
**Session Status:** Fases 0–10 completadas + Deploy verificado (60 tests, ruff limpio)
**Next Action:** Usar `appimage-builder` / `appimage-builder-gui` instalados