# Plan Detallado — MOD MAKER para Factorio

**Versión del plan:** 1.0  
**Fecha:** 24 de octubre de 2026  
**Idioma de interacción:** español  
**Idioma de código y nomenclatura:** inglés (norma §53)  
**Sistema de normas aplicado:** `AI_SOFTWARE_ENGINEERING_SYSTEM.md` (versión 1.1)  
**Juego objetivo:** Factorio (motor personalizado en C++ con Allegro para gráficos)

---

## 1. Resumen ejecutivo

Se desea construir una herramienta llamada **"Mod_Maker"** que permita:

1. Crear mods nuevos para Factorio.
2. Editar mods ya creados (extraer contenido y reconstruir mods extraídos).
3. Gestionar mods instalados por juego (mod manager para Factorio).
4. Funcionar con interfaz gráfica en macOS, Windows y Linux.
5. Ser extensible para agregar futuras mejoras y funciones (soporte para otros juegos mediante plugins).

Este plan analiza la viabilidad, recomienda la arquitectura núcleo + plugins, y define una hoja de ruta incremental por fases, completamente alineada con el `AI_SOFTWARE_ENGINEERING_SYSTEM.md`.

---

## 2. Análisis de viabilidad y recomendación

### 2.1 Las tres opciones evaluadas

| Criterio | Opción A: Multijuego unificado | Opción B: Por grupos de juegos similares | Opción C: Por juego individual |
|---|---|---|---|
| **Viabilidad técnica inicial** | Muy baja. Cada juego tiene formatos, motores y estructuras distintas. | Alta. Núcleo reutilizable + plugins por motor/grupo. | Muy alta por juego, pero esfuerzo acumulado elevado. |
| **Esfuerzo de desarrollo** | Extremadamente alto. | Medio. | Alto acumulado. |
| **Mantenibilidad** | Mala. | Buena. Plugins aislados. | Buena por juego, con duplicación. |
| **Extensibilidad** | Baja. | Alta. Nuevos plugins sin tocar el núcleo. | Media. |
| **Tiempo a MVP** | 12+ meses. | 4–6 meses núcleo + primer grupo. | 1–2 meses por juego. |

### 2.2 Conclusión de viabilidad

**Una herramienta "multijuego unificado" no es viable como punto de partida.**

**Recomendación:** enfoque híbrido — un **núcleo común multiplataforma** (GUI, mod manager, configuración, internacionalización, sistema de plugins) con **extensiones tipo plugin por motor o grupo de juegos similares**. El primer plugin será específico para **Factorio** (archivos `.zip` con `info.json`, `data.lua`, etc.). Posteriormente se podrán agregar plugins para otros grupos (Unity, Unreal, Source, PAK genérico).

---

## 3. Requisitos

### 3.1 Requisitos funcionales (RF)

| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | La aplicación debe iniciar en Windows, macOS y Linux sin instalación manual previa de dependencias por parte del usuario. | Crítica |
| RF-02 | Interfaz gráfica con temas claro y oscuro explícitos (nunca el tema nativo como "claro"). | Crítica |
| RF-03 | Crear un mod nuevo para Factorio: seleccionar archivos/carpetas, definir metadatos (`info.json`, nombre, autor, versión) y empaquetar en archivo `.zip`. | Alta |
| RF-04 | Extraer contenido de un mod de Factorio existente a una carpeta de trabajo editable. | Alta |
| RF-05 | Reconstruir (reempaquetar) un mod extraído y modificado, validando integridad antes de guardar. | Alta |
| RF-06 | Mod manager para Factorio: listar mods instalados, habilitar/deshabilitar, desinstalar y detectar conflictos básicos. | Alta |
| RF-07 | Sistema de plugins de soporte por juego/grupo, para añadir nuevos juegos sin modificar el núcleo. | Alta |
| RF-08 | Internacionalización: interfaz y mensajes en español e inglés por defecto, con carga dinámica de idiomas. | Alta |
| RF-09 | Logs de operaciones y barra de estado con retroalimentación al usuario durante tareas de I/O largas. | Media |
| RF-10 | Copia de seguridad automática antes de modificar un mod instalado. | Media |
| RF-11 | Validación de entradas: rutas, nombres de archivo y metadatos deben validarse antes de escribir en disco. | Alta |
| RF-12 | Posible integración futura con repositorios de mods (Factorio Mod Portal, Nexus Mods, etc.). | Baja (futuro) |

### 3.2 Requisitos no funcionales (RNF)

| ID | Requisito | Métrica / Criterio |
|---|---|---|
| RNF-01 | Multiplataforma | Ejecutable en Windows 10/11, macOS 12+, Ubuntu 22.04+ |
| RNF-02 | Mantenibilidad | Arquitectura modular, sin God Objects, dependencias acíclicas |
| RNF-03 | Testabilidad | Al menos pruebas unitarias para núcleo y extractores |
| RNF-04 | Seguridad | No ejecutar código arbitrario de mods; validar rutas para evitar path traversal |
| RNF-05 | Reproducibilidad | Build y pruebas reproducibles con versiones de dependencia fijadas |
| RNF-06 | Arranque sin fricción | Lanzador `run.sh` / `run.bat` que crea entorno, instala dependencias y ejecuta |
| RNF-07 | Distribución | Instaladores por SO: MSIX (Windows), DMG (macOS), AppImage/DEB (Linux) |

---

## 4. Decisiones arquitectónicas (ADR)

Se crearán los siguientes ADR en `docs/decisions/`:

- **ADR-001 — Arquitectura híbrida núcleo + plugins:** Justificar por qué se rechaza el multijuego unificado y se elige núcleo común + plugins por grupo de juegos.
- **ADR-002 — Stack tecnológico:** Justificar Python, PySide6, empaquetado y formato de configuración.
- **ADR-003 — Formato de paquete de mod de Factorio:** Definir estructura `info.json`, `data.lua`, empaquetado ZIP, metadatos.
- **ADR-004 — Seguridad de extracción/reconstrucción:** Reglas de sandbox para evitar path traversal y ejecución de código remoto.

Cada ADR seguirá el formato: Contexto, Problema, Opciones consideradas, Decisión, Consecuencias, Estado.

---

## 5. Stack tecnológico recomendado

| Capa | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.11+ | Manipulación de bytes/archivos sencilla, ecosistema rico, multiplataforma nativa, fácil de extender con plugins |
| GUI | PySide6 (Qt for Python) | Multiplataforma real (Win/macOS/Linux), temas claro/oscuro explícitos, QSettings, hilos para I/O, statusbar y menús base (norma §58) |
| Empaquetado / distribución | PyInstaller o Nuitka + instaladores por plataforma (MSIX, DMG, AppImage/DEB) | Permite entregar ejecutables autónomos por sistema operativo |
| Configuración | TOML (archivo `config.toml`) + variables de entorno | Separación de configuración y código (norma §13), sin valores mágicos ni rutas absolutas |
| Internacionalización | Archivos JSON dinámicos en `src/lang/lang_xx.json` | Español por defecto con fallback; agregar idioma = añadir archivo, cero cambios de código (norma §57) |
| Build / lanzador | `run.sh` y `run.bat` + `requirements.txt` | Arranque sin fricción (norma §56) |
| Testing | pytest | Pruebas unitarias, de integración y funcionales (norma §19) |
| Lint / tipo | ruff + mypy | Calidad de código y type checking (norma §20) |

---

## 6. Arquitectura modular y estructura de directorios

### 6.1 Principios aplicados (normas §10, §11, §47)

- Separation of Concerns: lógica de negocio separada de infraestructura y presentación.
- Composition over Inheritance: los plugins se componen al núcleo, no heredan de clases monolíticas.
- No God Objects ni estado global innecesario.
- Dependencias acíclicas: el núcleo no depende de plugins; los plugins dependen del núcleo.
- Configuración separada del código.

### 6.2 Estructura de directorios (norma §54)

```
Mod_Maker/
├── run.sh                      # Lanzador Linux/macOS (norma §56)
├── run.bat                     # Lanzador Windows (norma §56)
├── requirements.txt            # Manifiesto de dependencias (norma §56)
├── system-packages.txt         # Paquetes del sistema no instalables por pip (norma §56)
├── pyproject.toml              # Configuración del proyecto
├── README.md                   # Puerta de entrada (norma §31, §55)
├── CHANGELOG.md                # Registro de cambios
├── LICENSE
├── src/
│   ├── __init__.py
│   ├── core/                   # Lógica de negocio del núcleo (independiente de GUI)
│   │   ├── __init__.py
│   │   ├── config.py           # Carga de configuración (TOML/env)
│   │   ├── mod.py              # Modelo de datos de un mod
│   │   ├── manager.py          # Mod manager base (listar, habilitar, deshabilitar)
│   │   ├── extractor.py        # Interfaz de extracción de mods
│   │   ├── builder.py          # Interfaz de reconstrucción/empaquetado
│   │   ├── plugin_system.py    # Registro y carga de plugins de juego
│   │   ├── security.py         # Validación de rutas, sandbox, path traversal
│   │   ├── i18n.py             # Carga dinámica de traducciones
│   │   └── logger.py           # Configuración de logging (norma §18)
│   ├── gui/                    # SOLO estructura de GUI (norma §54)
│   │   ├── __init__.py
│   │   ├── main_window.py      # Ventana principal con menús base, statusbar, temas
│   │   ├── themes/             # Temas claro y oscuro explícitos (QSS)
│   │   ├── widgets/            # Widgets reutilizables
│   │   ├── dialogs/            # Diálogos (crear mod, extraer, configuración)
│   │   ├── styles.qss          # Hojas de estilo
│   │   └── resources/          # Iconos, imágenes
│   ├── lang/                   # Internacionalización (norma §57)
│   │   ├── lang_es.json        # Español por defecto
│   │   ├── lang_en.json        # Inglés
│   │   └── lang_xx.json        # Idiomas adicionales (carga dinámica)
│   └── plugins/                # Plugins de soporte por grupo de juegos
│       ├── __init__.py
│       ├── base_plugin.py      # Clase base que todo plugin debe implementar
│       └── factorio_group/     # Plugin específico para Factorio
│           ├── __init__.py
│           └── factorio_plugin.py
├── data/                       # Datos de ejemplo, plantillas de mod, esquemas
│   ├── templates/
│   └── schemas/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/               # Archivos de prueba (no mods reales con copyright)
├── docs/
│   ├── architecture/
│   ├── development/
│   ├── api/
│   ├── configuration/
│   ├── deployment/
│   ├── testing/
│   ├── troubleshooting/
│   ├── decisions/              # ADR-001, ADR-002, etc. (norma §32)
│   └── changelog/
├── locales/                    # Alias o copia de src/lang si se prefiere estándar (norma §14)
└── scripts/                    # Scripts de utilidad (build, release)
```

---

## 7. Diseño de componentes principales

### 7.1 Núcleo (`src/core/`)
- **ConfigManager:** carga `config.toml` y variables de entorno; expone valores tipificados.
- **ModManager:** operaciones de alto nivel sobre mods instalados por Factorio (listar, activar, desactivar, eliminar, detectar conflictos).
- **PluginSystem:** descubre, carga y descarga plugins en `src/plugins/`.
- **SecurityValidator:** previene path traversal, valida extensiones permitidas, bloquea ejecución de scripts dentro de mods.
- **I18nManager:** carga archivos JSON de idioma con fallback a español e inglés; detección de claves faltantes u huérfanas (norma §57).

### 7.2 Interfaz gráfica (`src/gui/`)
- **MainWindow:** menú base (Archivo, Juegos, Mods, Ayuda), barra de estado, pestañas por juego, tema claro/oscuro explícito.
- Hilos de trabajo (QThread / QRunnable) para todas las operaciones de I/O para no bloquear la GUI (norma §58).
- Diálogos: "Nuevo mod", "Extraer mod", "Reconstruir mod", "Gestionar mods de Factorio", "Configuración", "Idioma".
- Todos los textos de interfaz pasan por `translate("clave")`; ninguno incrustado directamente en lógica (norma §14).

### 7.3 Plugin de Factorio (`src/plugins/factorio_group/`)
Factorio distribuye mods como archivos `.zip` que contienen al menos:
- `info.json`: metadatos del mod (nombre, versión, autor, factorio_version, dependencias).
- `data.lua`, `data-updates.lua`, `data-final-fixes.lua`: lógica del mod.
- Gráficos, sonidos, etc.

El plugin de Factorio implementa:
- Detección de la carpeta de mods de Factorio por SO (`~/factorio/mods` en Linux, `%APPDATA%/Factorio/mods` en Windows, `~/Library/Application Support/factorio/mods` en macOS).
- Lectura/escritura de `info.json`.
- Empaquetado/desempaquetado ZIP respetando la estructura de Factorio.
- Validación de metadatos antes de empaquetar.

---

## 8. Plan de implementación por fases (incremental, norma §21)

Cada fase entrega un incremento verificable y termina con validación (build, tests, lint).

### Fase 0 — Investigación y validación de viabilidad (2–4 semanas)
- Investigar formato de mods de Factorio (`info.json`, estructura ZIP, versiones de Factorio compatibles).
- Validar que PySide6 empaqueta correctamente en los tres SO.
- Definir el esquema de metadatos del mod.
- Entregable: ADR-001, ADR-002, ADR-003, ADR-004.

### Fase 1 — Núcleo multiplataforma y GUI base (4–6 semanas)
- Lanzador `run.sh` / `run.bat` + `requirements.txt` (arranque sin fricción).
- `src/core/config.py`, `src/core/i18n.py`, `src/core/logger.py`.
- `src/gui/main_window.py` con menús base, temas claro/oscuro, statusbar.
- Soporte de idiomas español e inglés (archivos JSON).
- Pruebas unitarias de configuración e i18n.
- Entregable: aplicación arranca en Win/macOS/Linux, cambia idioma y tema.

### Fase 2 — Mod manager para Factorio (3–4 semanas)
- `src/core/manager.py`: registro de Factorio, carpeta de mods por SO.
- GUI: listar mods instalados, habilitar/deshabilitar, desinstalar.
- Copia de seguridad automática antes de modificar mods instalados (RF-10).
- Pruebas de integración del mod manager.
- Entregable: se pueden agregar y ver los mods instalados de Factorio.

### Fase 3 — Motor de extracción y reconstrucción + SDK de plugins (4–6 semanas)
- `src/core/extractor.py`, `src/core/builder.py`, `src/core/plugin_system.py`.
- `src/plugins/base_plugin.py` y plugin de Factorio (`factorio_group/factorio_plugin.py`).
- Operaciones de extraer y reconstruir con progreso en barra de estado y logs.
- Validación de seguridad (path traversal, extensiones peligrosas).
- Entregable: se puede extraer un mod de Factorio, editar archivos y reconstruirlo.

### Fase 4 — Creador de mods nuevos para Factorio (3–4 semanas)
- GUI: asistente para crear mod (seleccionar archivos, metadatos `info.json`, versión de Factorio).
- Empaquetado en archivo `.zip` según el plugin de Factorio.
- Validación de metadatos antes de generar el paquete.
- Entregable: se puede crear un mod nuevo para Factorio desde cero y empaquetarlo.

### Fase 5 — Pulido, empaquetado multiplataforma y distribución (4–8 semanas)
- Instaladores por plataforma: MSIX (Windows), DMG (macOS), AppImage/DEB (Linux).
- Pruebas con mods de prueba (sin usar contenido con derechos de autor sin permiso).
- Documentación en `docs/`, pruebas funcionales finales, corrección de bugs.
- Entregable: versión 1.0 lista para distribuir.

**Duración estimada total del MVP:** aproximadamente 6 a 9 meses.

---

## 9. Internacionalización (normas §14 y §57)

- Idiomas por defecto: español (`es`) e inglés (`en`).
- Archivos JSON separados en `src/lang/lang_xx.json` con carga dinámica.
- Español como idioma por defecto con fallback; cada clave debe existir en todos los idiomas (verificado por tests, sin huérfanas ni faltantes).
- Al agregar una cadena traducible: añadir al idioma principal, añadir traducción en español e inglés, mantener consistencia de claves.
- Textos de interfaz nunca incrustados en la lógica: usar `translate("menu.settings")`.

---

## 10. Seguridad (norma §25)

- Validación de todas las entradas de usuario (rutas, nombres de archivo, metadatos).
- Prevención de path traversal al extraer archivos de mods.
- Bloqueo de ejecución de scripts o binarios dentro de carpetas de mods sin validación explícita.
- No se almacenan secretos ni credenciales en el código ni en el repositorio (norma §13).
- Los logs nunca registran información sensible (norma §18).
- Los mods no se ejecutan; solo se empaquetan, extraen y gestionan como archivos de datos.

---

## 11. Testing (norma §19)

- **Unitarias:** componentes individuales del núcleo (config, i18n, security validator, plugin loader).
- **Integración:** interacción entre mod manager y plugin de Factorio; extraer → editar → reconstruir.
- **Funcionales:** flujo completo desde la GUI (crear mod, instalar, habilitar/deshabilitar).
- **Regresión:** garantizar que nuevas funciones no rompan el mod manager existente.
- **Errores:** rutas inválidas, archivos corruptos, disco lleno, permisos denegados.
- No se escriben pruebas artificiales solo para aumentar cobertura (norma §19).

---

## 12. Documentación (normas §30, §31, §33, §55)

- **README.md:** nombre, descripción, características, requisitos, instalación, uso paso a paso (comandos copiables), qué esperar, si algo falla, punto de entrada, configuración, desarrollo, testing, estructura, contribución, licencia.
- **docs/:** architecture, development, api, configuration, deployment, testing, troubleshooting, decisions, changelog.
- **CHANGELOG.md:** registro de cambios por versión.
- **ADRs:** decisiones arquitectónicas importantes.
- Cada cambio que modifique API, configuración, instalación o comportamiento actualiza la documentación correspondiente (norma §33).

---

## 13. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Cambios en la API de mods de Factorio rompen el plugin | Media | Plugin aislado; versionar soporte por versión de Factorio; retrocompatibilidad (norma §27). |
| Uso de contenido con derechos de autor sin permiso | Alta | No incluir mods reales con copyright en el repositorio; usar solo archivos de prueba propios; advertir al usuario en la documentación. |
| Rendimiento bajo en archivos grandes | Media | Medición antes de optimización (norma §26). |
| Empaquetado multiplataforma falla en algún SO | Media | Probar build en los tres SO en cada release. |
| Integración con Factorio Mod Portal / Nexus Mods | Baja | Dejarse para fase futura (RF-12); no bloquear el MVP. |

---

## 14. Criterios de finalización (norma §43)

Una fase se considera terminada cuando:

- [ ] Requisitos de la fase implementados
- [ ] Código revisado (code review)
- [ ] Tests ejecutados (unitarias, integración, funcionales cuando corresponda)
- [ ] Build/compilación verificada en Windows, macOS y Linux
- [ ] Errores corregidos
- [ ] Seguridad revisada (validación de entradas, path traversal, logs sin secretos)
- [ ] Dependencias revisadas (licencias, seguridad, versiones fijadas)
- [ ] Traducciones actualizadas (español e inglés completos, sin claves huérfanas)
- [ ] Documentación actualizada (README, docs, CHANGELOG)
- [ ] Deuda técnica revisada
- [ ] Cambios no relacionados evitados
- [ ] Estado final verificado: la aplicación arranca y la funcionalidad de la fase funciona

Si alguna casilla no puede cumplirse, se indicará explícitamente (norma §42).

---

## 15. Respuestas a preguntas del usuario

1. **Juego:** Factorio (motor personalizado en C++ con Allegro para gráficos).
2. **Confirmado:** Sí, Factorio.
3. **Distribución:** Implementación y pruebas con `run.sh`/`run.bat`, pero se implementará distribución como instaladores por SO (MSIX para Windows, DMG para macOS, AppImage/DEB para Linux).
4. **Integración con tiendas:** Sí, es posible; se contempla como requisito futuro (RF-12) para Factorio Mod Portal, Nexus Mods, etc., sin bloquear el MVP.

---

## 16. Referencias a normas aplicadas

Este plan sigue el `AI_SOFTWARE_ENGINEERING_SYSTEM.md` v1.1, en particular:

- §2 Idioma (español en interacción; inglés en código).
- §3 Principios (KISS, DRY, YAGNI, SOLID, Separation of Concerns, Composition over Inheritance, Explicit over implicit, simplicidad antes que sobreingeniería).
- §5 Fase 0 — Descubrimiento.
- §9 Planificación.
- §10 Arquitectura modular.
- §11 Responsabilidad de los módulos.
- §12 Dependencias.
- §13 Configuración separada del código; sin credenciales en repositorio.
- §14 y §57 Internacionalización (español e inglés por defecto, archivos JSON dinámicos, fallback).
- §17 Manejo de errores.
- §18 Logging.
- §19 Testing.
- §20 Validación.
- §21 Desarrollo incremental.
- §23 Refactorización.
- §24 Deuda técnica.
- §25 Seguridad.
- §26 Performance (no optimización prematura).
- §27 y §28 Compatibilidad y migraciones.
- §29 Git y control de cambios.
- §30, §31, §33 Documentación.
- §32 ADRs.
- §42 No ocultar problemas.
- §43 Criterios de finalización.
- §44 Informe final obligatorio.
- §45 Regla de continuidad.
- §46 Reglas de prioridad.
- §47 Anti-patrones.
- §48 Decisión técnica.
- §49 Regla maestra y §50 Principio final.
- §53 Nombres funcionales en inglés.
- §54 Estructura por funciones (`src/gui/`, `src/core/`, `src/lang/`, `data/`, `tests/`).
- §55 README operativo.
- §56 Arranque sin fricción (`run.sh`/`run.bat`, `requirements.txt`, `system-packages.txt`).
- §58 Stack GUI y plantillas (temas claro/oscuro explícitos, hilos para I/O, QSettings, log + statusbar, menús base).

---

## 17. Características implementadas de herramientas de referencia

Se integraron funcionalidades de tres referentes de mods de Factorio:

### 17.1 Langbergio/Factorio-Mod-Creator-Studio (GitHub)
- **Formularios sin código** para crear items, tecnologías y recetas (`NewItemDialog`, `PrototypeGenerator`)
- **Editor Lua** con resaltado de sintaxis y autocompletado (planificado en `LuaEditorDialog`)
- **Generador de sprite sheets** (`SpriteSheetDialog`, `SpriteSheetGenerator` — requiere Pillow)
- **Export ZIP con un clic** (`ExportModDialog`, `FactorioExporter`)
- **JS → Lua translation** (planificado, fase avanzada)

### 17.2 Supercraft Factorio Mod Generator (supercraft.host)
- **Generador de mods para servidor** sin código (`TweakGenerator`, `TweaksDialog`)
- **Sliders de tweaks**: velocidad de crafting, coste de recetas, tamaño de pilas, velocidad de minería, salud del jugador
- **Generación de `data-final-fixes.lua`** automática
- **Soporte Factorio 2.0 / 2.1** (`ModMetadata.factorio_version`)

### 17.3 justarandomgeek/factoriomod-debug (VS Code Marketplace)
- **Validación JSON de `info.json`** (`FactorioValidator`, `data/schemas/info_json_schema.json`)
- **Language support** para archivos de locale y changelog (planificado)
- **Packaging and publishing** (`FactorioExporter` → `mod_packager.build_mod_zip()`, exportación a `.zip`)
- **Debug Adapter** (planificado, fase avanzada con `LuaDebugAdapter`)

### 17.4 Unificación de empaquetado (DRY)
Se eliminó la duplicación entre "Reconstruir mod", "Exportar ZIP con un clic" y "Packaging and publishing". Todas usan ahora la misma función:

- **`src/core/mod_packager.py`** — `build_mod_zip()`: función única de empaquetado que valida `info.json`, bloquea extensiones peligrosas y crea el `.zip`
- Usada por: `FactorioPlugin.build()`, `FactorioExporter.export_zip()`, `FactorioExporter.export_from_directory()`
- **RebuildModDialog** y **ExportModDialog** comparten el mismo motor de empaquetado, solo difieren en el flujo de usuario (uno reconstruye desde carpeta extraída, otro exporta un mod en memoria)

### 17.5 Gestión de archivos y editor avanzado (Fase 7 - COMPLETADA)
- **`src/core/mod_file_manager.py`** — `ModFileManager`: crear, eliminar, renombrar archivos y carpetas dentro del mod con validación de seguridad (path traversal)
- **`src/core/syntax_highlighter.py`** — `SyntaxHighlighterFactory` y highlighters para Lua, JSON, TOML, CFG y texto plano
- **`src/core/lua_api.py`** — Definición de API de Factorio (funciones, eventos, tipos)
- **`src/gui/widgets/edit_mod_tab.py`** — `EditModTab` con:
  - Vista previa de imágenes (.png, .jpg, .jpeg, .bmp, .gif, .webp, .tga)
  - Edición de archivos de texto con syntax highlighting
  - Botones: Crear archivo, Crear carpeta, Renombrar, Eliminar
  - Botones: Guardar Cambios, Reconstruir Mod, Cerrar
  - Menú contextual (clic derecho) para operaciones rápidas
  - Listado de archivos con iconos indicativos ([T] texto, [I] imagen, [D] carpeta, [ ] otro)
- **`src/gui/widgets/lua_completer.py`** — Autocompletado de API de Factorio
- **`src/gui/dialogs/lua_editor_dialog.py`** — `LuaEditorDialog` con editor Lua integrado

### 17.6 Editor Lua con autocompletado (Fase 8 - EN PROGRESO)
- **`src/core/lua_api.py`** — Definición de API de Factorio (funciones, eventos, tipos)
- **`src/core/syntax_highlighter.py`** — SyntaxHighlighter para Lua, JSON, CFG y texto plano
- **`src/gui/widgets/lua_completer.py`** — Autocompletado de API de Factorio
- **`src/gui/dialogs/lua_editor_dialog.py`** — Editor Lua integrado con extracción, edición y reconstrucción

### Archivos creados

| Categoría | Archivos |
|-----------|----------|
| Núcleo (src/core/) | `factorio_mod.py`, `factorio_validator.py`, `prototype_generator.py`, `tweak_generator.py`, `sprite_sheet_generator.py`, `factorio_export.py`, `mod_template.py`, **`factorio_validator.py`**, **`factorio_plugin.py`**, **`plugin_system.py`**, **`mod_packager.py`**, **`mod_file_manager.py`**, **`syntax_highlighter.py`**, **`lua_api.py`** |
| GUI (src/gui/dialogs/) | `new_item_dialog.py`, `tweaks_dialog.py`, `sprite_sheet_dialog.py`, `export_mod_dialog.py`, **`lua_editor_dialog.py`** |
| GUI (src/gui/widgets/) | `mod_operations_panel.py`, `mods_explorer_panel.py`, **`edit_mod_tab.py`**, **`lua_completer.py`** |
| Datos (data/) | `schemas/info_json_schema.json`, `templates/info_json_example.json`, `templates/README.md` |
| Pruebas (tests/unit/) | `test_factorio_mod.py`, `test_factorio_validator.py`, `test_prototype_generator.py`, `test_tweak_generator.py`, `test_mod_template.py`, **`test_mod_packager.py`**, **`test_mod_packager_nested.py`**, **`test_syntax_highlighter.py`** |

**Total de tests:** 78 (67 originales + 11 nuevos para syntax_highlighter), todos pasando.

---

## 18. Próximos pasos recomendados

1. **Fase 9 — Integración con Debug Adapter** (LuaDebugAdapter, factoriomod-debug) — **COMPLETADA** ✅
   - `src/core/debug_adapter.py`: interfaz base DebugAdapter, DebugSession, Breakpoint
   - `src/core/lua_debugger.py`: implementación LuaDebugAdapter (detección de líneas ejecutables, breakpoints, variables, output de consola)
   - `src/plugins/factorio_group/factorio_plugin.py`: integración de debug (create/start/pause/resume/stop_debug, set/remove_debug_breakpoint, get_debug_variables/output, validate_folder, is_debug_supported)
   - `src/gui/dialogs/debug_console_dialog.py`: consola de depuración GUI con:
     - Selector de mod (.zip o carpeta extraída, con detección automática de carpeta padre si se selecciona un archivo .lua)
     - Controles Iniciar/Pausar/Reanudar/Detener
     - Consola de salida de print() de Lua
     - Lista de breakpoints con agregar/eliminar
     - Panel de variables con agregar/editar/eliminar (tipos: int, float, bool, str, None)
     - Robustez ante cierre de diálogo (manejo de RuntimeError en widgets PySide6)
   - `tests/unit/test_debug_adapter.py`: 9 tests
   - `tests/unit/test_lua_debugger.py`: 10 tests
   - Total: 19 tests nuevos (97 total pasando)
2. **Fase 10 — CLI tipo `fmtk`** para operaciones por terminal — **COMPLETADA** ✅
   - `src/cli/mod_cli.py`: reescrito completamente con:
     - Comandos en inglés: create, extract, rebuild, install, uninstall, list, info
     - Nuevos comandos: debug (start/pause/resume/stop/list), variables (set/get/list/remove), breakpoints (add/remove/list)
     - Estilos de salida con emojis (✓, ✗, ⚠, ℹ, →) para mejor UX
     - Formato de tabla para información de mods (rich Table)
     - Help texts mejorados para todos los comandos y subcomandos
     - ASCII art logo (pyfiglet) al iniciar
     - Menú interactivo (questionary) cuando no se especifica comando
     - Barras de progreso (tqdm) en operaciones largas
     - Normas de CLI implementadas (§63-#67): colores, tablas, progreso, ASCII, menús interactivos
   - Todos los comandos probados y funcionando individualmente

3. **Núcleo de creación de mods pulido** (`src/core/factorio_mod.py`):
   - `ModMetadata` con validación completa según documentación oficial de Factorio
   - Validación de nombres: solo letras minúsculas, números, guiones; sin espacios; no empieza ni termina con guion
   - Validación de versión: formato número.número.número (ej. 1.0.0)
   - Validación de factorio_version obligatorio
   - `FactorioMod` con soporte para `data.lua`, `control.lua`, `data-final-fixes.lua`
   - Generación de código Lua para prototipos (items, tecnologías)
   - `ModValidationError` para errores específicos de validación

4. **Diálogo de crear mod mejorado** (`src/gui/dialogs/create_mod_dialog.py`):
   - Validación en tiempo real del nombre del mod
   - Validadores de expresión regular para nombre y versión
   - Campos adicionales: título, autor, descripción, factorio_version, homepage, dependencias
   - Mensajes de ayuda y tooltips explicativos
   - Información sobre estructura de carpetas de mods
   - Botón Crear solo habilitado cuando todo es válido
3. **Fase 11 — Empaquetado multiplataforma** (MSIX, DMG, AppImage)
4. **Fase 12 — JS → Lua translation** (opcional)

Una vez respondidas las preguntas de la sección 15, se puede proceder a redactar los ADR y continuar con las fases siguientes.

---

## 19. Regla de revisión periódica (cada 3 fases)

Cada 3 fases de desarrollo, se debe:

1. Volver a leer el `AI_SOFTWARE_ENGINEERING_SYSTEM.md` para verificar que el proyecto sigue alineado con todas las normas.
2. Revisar todo el código implementado para identificar duplicaciones, código muerto o sobreingeniería.
3. Revisar y ejecutar todos los tests para garantizar que nada se ha roto.
4. Revisar la documentación para asegurar que esté actualizada con los cambios realizados.
5. Refactorizar cualquier código que se haya vuelto innecesariamente complejo o duplicado.

Esta regla evita que el proyecto se desvíe de sus principios originales y mantiene la calidad del código a lo largo del tiempo.

---

## 20. Revisión, pulido y factorización periódica (cada 3 fases)

Dependiendo del proyecto, cada 3 fases de desarrollo se debe:

1. Releer el `AI_SOFTWARE_ENGINEERING_SYSTEM.md` para verificar que el proyecto sigue alineado con todas las normas y no pierde coherencia.
2. Revisar todo el código implementado para identificar duplicaciones, código muerto, sobreingeniería o archivos huérfanos.
3. Revisar y ejecutar todos los tests para garantizar que nada se ha roto.
4. Revisar la documentación para asegurar que esté actualizada con los cambios realizados.
5. Pulir y factorizar cualquier código que se haya vuelto innecesariamente complejo, duplicado o que ya no se utilice.

Esta norma se aplica además de la regla #19 para garantizar que el proyecto se mantenga lo más limpio posible a lo largo del tiempo.

---

## 21. Evitar bucles de respuesta redundante

Se debe evitar realizar muchas iteraciones a respuestas redundantes o entrar en bucles cerrados donde el agente repite el mismo razonamiento sin avanzar.

- Si después de realizar 3 iteraciones similares sobre un mismo punto el usuario sigue diciendo simplemente "continúa" o equivalente sin dar una dirección nueva, el agente debe **detenerse y hacer preguntas al usuario** para obtener una dirección concreta antes de seguir.
- No se debe asumir que "continúa" significa avanzar automáticamente a la siguiente fase del plan sin confirmación.
- El agente debe ofrecer opciones claras y esperar la decisión del usuario para evitar bucles de retroalimentación vacía.

Esta norma garantiza que el proyecto avance con propósito y no se quede estancado en repeticiones sin valor agregado.

---

## 22. Snapshot del proyecto antes de cambios importantes

Antes de realizar cualquier cambio significativo en el código (implementación de nuevas funcionalidades, refactorización, eliminación de archivos, cambios en arquitectura, etc.), se debe crear un **snapshot del estado actual del proyecto** para poder regresar a una instancia anterior si el cambio falla o introduce regresiones.

El snapshot debe incluir:

1. **Copia de seguridad del estado actual**: crear una copia del directorio del proyecto o utilizar control de versiones (git commit, git tag, o copia de seguridad manual en directorio con timestamp).
2. **Ejecución de tests antes del cambio**: verificar que todos los tests pasan antes de iniciar cualquier modificación.
3. **Documentar el cambio planeado**: anotar qué se va a modificar, por qué y qué se espera lograr.
4. **Verificación posterior al cambio**: después de aplicar el cambio, ejecutar nuevamente todos los tests y verificar que la funcionalidad no se ha roto.
5. **Rollback si es necesario**: si el cambio introduce errores o regresiones, restaurar el snapshot inmediatamente y reevaluar el enfoque.

Esta norma protege al proyecto contra cambios que puedan romper la funcionalidad existente y permite una recuperación rápida ante problemas inesperados.

---

## 23. Colores y estilos de texto en CLI

Usar colores en la terminal para diferenciar tipos de mensajes:

- **Rojo**: Errores y fallos críticos
- **Amarillo**: Advertencias
- **Azul**: Información general
- **Verde**: Éxitos y operaciones completadas

Implementación por lenguaje:

- **Python**: `colorama`, `rich` o `typer`
- **Node.js/JavaScript**: `chalk` o `kleur`
- **C/C++**: Códigos de escape ANSI o `ncurses`

Ejemplo (Python con rich):
```python
from rich import print
print("[red]Error:[/red] No se pudo completar la operación")
print("[green]✓[/green] Operación completada correctamente")
print("[yellow]⚠[/yellow] Advertencia: acción no recomendada")
print("[blue]ℹ[/blue] Información adicional disponible")
```

---

## 24. Tablas y cajas estructuradas en CLI

Organizar datos en filas y columnas con bordes limpios en lugar de texto plano para mejorar la lectura:

- **Python**: `rich` (tablas con bordes) o `tabulate`
- **Node.js**: `cli-table3`

Ejemplo (Python con rich):
```python
from rich.table import Table
table = Table(title="Mods instalados")
table.add_column("Nombre", style="cyan")
table.add_column("Versión", style="magenta")
table.add_row("MiMod", "1.0.0")
print(table)
```

---

## 25. Barras de progreso y indicadores de carga en CLI

Mostrar indicadores visuales cuando el programa procesa algo que tome segundos o minutos:

- **Python**: `tqdm` o `rich.progress`
- **Node.js**: `ora` (spinners) o `cli-progress`

Ejemplo (Python con tqdm):
```python
from tqdm import tqdm
import time

for i in tqdm(range(100), desc="Procesando mod..."):
    time.sleep(0.01)
```

Ejemplo (Python con rich.progress):
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Extrayendo...", total=100)
    while not progress.finished:
        progress.update(task, advance=10)
```

---

## 26. Arte ASCII y Logos en CLI

Incluir un encabezado con logo o nombre de la herramienta en texto grande (figlet/banner) al iniciar el programa para mejorar la identidad visual:

- **Python**: `pyfiglet` o `banner`
- **Node.js**: `figlet` o `cli-banner`

Ejemplo (Python con pyfiglet):
```python
from pyfiglet import Figlet
f = Figlet(font='slant')
print(f.renderText('Mod Maker'))
```

---

## 27. Menús interactivos en CLI

Ofrecer menús con flechas para seleccionar opciones en lugar de obligar al usuario a recordar todos los comandos y argumentos:

- **Python**: `questionary` o `InquirerPy`
- **Node.js**: `inquirer`

Ejemplo (Python con questionary):
```python
import questionary

opcion = questionary.select(
    "¿Qué deseas hacer?",
    choices=["Crear mod", "Extraer mod", "Reconstruir mod", "Salir"]
).ask()
```

---

Una vez respondidas las preguntas de la sección 15, se puede proceder a redactar los ADR y continuar con las fases siguientes.

