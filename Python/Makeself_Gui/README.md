# Makeself GUI

Creador e inspector gráfico de archivos auto-extraíbles Makeself. Stack: Python + PySide6. Creador multiplataforma (Linux/Win/Mac), salida solo Unix.

## Requisitos

- Python 3.11+
- Sistema: `bash tar gzip makeself` (ver `system-packages.txt`)
- Solo `pip install -r requirements.txt` (lo hace `run.sh` solo)

## Uso paso a paso

```bash
./run.sh
./run.sh --lang en --theme dark
python -m pytest -q
```

1. Pestaña Crear: elige directorio, salida `.run`, etiqueta, script inicial, compresor → Crear.
2. Pestaña Inspeccionar: abre un `.run` → `--info`/`--check` → Extraer `--noexec` a `/tmp/reconstruido`.
3. Pestaña Plantillas y Append: genera esqueleto `console`/`zenity`/`mojosetup`/`universal`/`graphical` (crea `data/` + script inicial) o añade una carpeta extra a un `.run` existente con `--append`.
   - `universal`: instalador genérico multijuego — `./setup.sh [DESTINO] [--link] [--desktop]`, `--list`, genera `uninstall.sh`, tolera espacios.
   - `graphical`: asistente con zenity (verificación SHA256/MD5 visible, info del paquete, elegir destino, progreso %, accesos, ejecutar al final); sin GUI usa modo consola.
   - Flags del instalador tras `--`: `./juego.run -- DESTINO [--link] [--desktop] [--nogui] [--skip-verify]`.
4. Modifica archivos → se guarda `proyecto.msgui.json` → recrea desde Crear.

## Qué esperar

- Artefactos: `*.run` auto-extraíble, `proyecto.msgui.json`, logs en GUI + statusbar.
- Temas explícitos claro/oscuro en Ver. Idioma es/en en Ver (requiere reinicio).
- Preferencias persistidas con QSettings.

## Si algo falla

- `Faltan dependencias: bash/makeself`: instala según `system-packages.txt`.
- `archive_dir no existe`: el directorio debe existir antes de crear.
- En Windows: ejecuta dentro de Git-Bash o instala MSYS2; `makeself` exige shell Unix.
- Archivos >2GB: `--check` tarda; la GUI no se congela (hilos QThread).
- Al **crear** en `/tmp` pequeño: cambia el campo Directorio temporal a un disco con ~2x el tamaño.
- Al **instalar** un `.run` grande con `/tmp` lleno: `TMPDIR=/disco/con/espacio ./app.run`
  (o `./app.run --target /disco/con/espacio/extraccion`). El instalador además
  re-pide destino si la carpeta elegida no tiene espacio.

## Punto de entrada

`src/app.py` → `MainWindow` en `src/gui/main_window.py`. Lógica en `src/core/`, idiomas en `src/lang/lang_xx.json`, temas en `src/themes/`.

## Estructura

```text
src/gui/ src/core/ src/lang/ src/themes/ data/ tests/ docs/decisions/
```
