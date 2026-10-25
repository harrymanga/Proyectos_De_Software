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
