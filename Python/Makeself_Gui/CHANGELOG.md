# CHANGELOG

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
