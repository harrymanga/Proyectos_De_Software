# CHANGELOG

## 0.5.4 — Binario mojosetup solo-stdio (sin pantalla azul)

- El binario vendorizado `mojosetup` se recompila con **solo GUI stdio** (ncurses,
  GTK3, Cocoa y WWW deshabilitados). Así el instalador nunca intenta abrir una
  ventana gráfica y no se queda en pantalla azul en entornos sin DISPLAY.
- `scripts/build_mojosetup.sh` compila por defecto solo stdio; `--gui all` ya no
  incluye ncurses ni GTK3. `--gui ncurses` y `--gui gtk3` quedan como opciones
  explícitas con advertencia.
- El usuario debe **regenerar sus `.sh`/`.bin` existentes** desde la app para que
  usen el nuevo binario sin GTK3.

## 0.5.3 — Fix: plugin Gtk3 provocaba PANIC
- El plugin Gtk3 vendorizado hacía que el instalador-MojoSetup terminara en PANIC (`fatal() called more than once`) y se quedara colgado. Gtk3 ya no se empaqueta por defecto.
- `build_mojosetup.sh --gui all` excluye Gtk3; queda opt-in con `--gui gtk3` y aviso.
- `plugin_warning()` avisa en la GUI si detecta un Gtk3 vendorizado.
- `detect_launcher`: prioriza `start.bash` y excluye `startmojo.sh` (residuo de MojoSetup) y `.desktop`.
- `_copy_gui_plugins`: no crea `guis/` vacío en el paquete.
- 57 tests.

## 0.5.2 — Progreso en la instalación MojoSetup
- Botón «Probar instalación»: ejecuta el instalador con barra de progreso real, archivo en curso y fases (extraer/manifiesto/completo).
- `mojo_install_worker.py` usa `pty` porque MojoSetup solo emite progreso si detecta un terminal.
- Parser de `archivo: N% (total progress: M%)` con 6 tests.

## 0.5.1 — Plugins GUI, ARM64 y --nodiskspace
- `build_mojosetup.sh --gui stdio|ncurses|gtk3|all`: plugins dinámicos en `guis/<arch>/`.
- Fix: los plugins GUI se empaquetan en la raíz del instalador, no en `data/` (evita instalarlos en la carpeta del usuario).
- `build_mojosetup_arm64.sh`: cross-compilación a ARM64 con toolchain aarch64.
- Casilla `--nodiskspace` en Crear: muestra el comando de ejecución correcto (es flag del stub, no del creador).
- CI: jobs de verificación de binarios vendorizados y de cross-compilación ARM64.
- 48 tests.

## 0.5.0 — Backend MojoSetup (sin staging en /tmp)
- `src/core/mojo_export.py`: genera `config.lua` + ZIP con `data/` y `scripts/`, anexado al binario `mojosetup`.
- Pestaña MojoSetup: origen, salida, ID, vendor, versión, destino fijo o a elegir, destinos recomendados, detección de lanzador.
- `scripts/build_mojosetup.sh` compila y vendoriza MojoSetup (zlib, commit fijado) en `data/vendor/mojosetup/`.
- 11 tests nuevos, incluido E2E que instala de verdad y verifica archivos + `uninstall.sh`.
- Documentación: `docs/mojosetup.md` y ADR-005.

## 0.4.3 — Aviso de espacio para quien instala
- Al crear, el log informa el espacio temporal que necesitará el instalador (~tamaño sin comprimir en TMPDIR).
- La plantilla `graphical` re-ejecuta `--check` sobre el `.run` con progreso y muestra las líneas reales (SHA256/MD5) en el diálogo de info; aborta si falla.
- `--skip-verify` para omitirlo. Nota: los flags del script se pasan tras `--` (`./juego.run -- DESTINO --link`).
- `graphical`: si el destino no tiene espacio, error zenity y re-selección de carpeta en bucle.
- `universal` y modo consola: abortan con mensaje claro en vez de fallar a mitad.
- App Crear: campo Directorio temporal (TMPDIR) + aviso previo de espacio (~2x en temporales).
- `setup.sh` con GUI zenity: info del paquete (tamaño, archivos, ejecutable, verificación), elegir destino, confirmación, progreso % real vía tar, preguntas de accesos, ejecutar al final.
- Sin DISPLAY/zenity o con `--nogui`: modo consola. 3 tests (sintaxis, consola, GUI con stub de zenity).

## 0.3.3 — Barra de progreso
- `QProgressBar` permanente en la statusbar: % real parseado de makeself, indeterminada cuando no hay %.
- Crear usa progreso por archivos (tar lista `a ./x`; Makeself no emite % al crear): 0-99% por conteo + 100% al terminar.
- Etiqueta de fase junto a la barra: CRC / SHA256 / MD5 / Verificando / Extrayendo / Comprimiendo (es/en).
- Workers con streaming (`Popen`) en Crear/Extraer/Check/Append; `--info` muestra ocupado.
- Log saneado (`clean_output`): emula `\b`/`\r` de terminal; lectura por bloques para % en vivo aunque venga sin `\n`.
- Botón … en `startup_script` con diálogo de archivo.
- Si el script está fuera de `archive_dir`, la app propone copiarlo dentro (Makeself lo exige) sin sobrescribir.
- `universal`: `setup.sh` genérico (data/ o carpeta completa, `--link/--desktop`, `uninstall.sh`, espacios OK, separador `--`, `exit 0` garantizado).
- Fix: `data/` vacía se ignora y se instala el resto (antes instalaba nada).
- Builder: `--nox11` por defecto para que el `.run` no intente abrir xterm.
- `src/core/templates.py`: esqueletos console/zenity/mojosetup-stub (documentado como simplificado).
- `src/core/append.py` + `AppendWorker`: `--append` desde la GUI sin bloquear.
- Tercera pestaña Plantillas y Append; `makeself-gui.spec`; CI matriz 3 SO; ruff.
- i18n ampliada (paridad es/en verificada).

## 0.2.0 — Estructura canónica + i18n + checklist GUI
- Estructura `src/gui|core|lang|themes`, `data/`, `docs/decisions/`.
- i18n dinámica es/en con test de paridad.
- Temas claro/oscuro explícitos, QSettings, statusbar, menús base, workers QThread.
- Lanzadores `run.sh`/`run.bat` + `requirements.txt` + `system-packages.txt`.
- README operativo y ADRs.

## 0.1.0 — Bootstrap
- Builder con paridad CLI, validator, inspector `--info/--noexec`, proyecto `.msgui.json`, wizard mínimo, 4 tests.
