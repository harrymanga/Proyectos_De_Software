# Backend MojoSetup

Genera instaladores que **no necesitan staging en `/tmp`**, a diferencia de Makeself.

## Por qué

Makeself extrae el payload completo a `$TMPDIR` antes de ejecutar el instalador. Con
`/tmp` como tmpfs pequeño (habitual en escritorios) un juego de varios GB falla con:

```text
Not enough space left in /tmp (3837756 KB) to decompress juego.run (7956092 KB)
```

Ese aviso lo emite el stub **antes** de la GUI, así que ninguna plantilla puede
preguntar por la carpeta. MojoSetup evita el problema: el binario se lee a sí mismo
como ZIP anexado y escribe directo al destino que elige el usuario.

## Uso

1. Un solo paso: compilar y vendorizar el binario.

```bash
scripts/build_mojosetup.sh
```

Deja en `data/vendor/mojosetup/`: `mojosetup`, `make_self_extracting`, `LICENSE.txt` y
`scripts/{mojosetup_init,mojosetup_mainline,localization}.lua`.

2. En la app, pestaña **MojoSetup**:
   - Directorio a empaquetar, salida, etiqueta, ID, vendor, versión.
   - *Detectar lanzador* rellena el lanzador (`start.sh`, `AppRun`…).
   - Destino vacío = el usuario lo elige al instalar; con valor = instalación silenciosa.
   - *Exportar instalador MojoSetup*.

## Notas de la config generada

`config.lua` se genera desde `src/core/mojo_export.py:build_config_lua`. Campos que
MojoSetup exige de forma explícita (si faltan, aborta con `NOTICE: BUG: Config ...`):
`genericname`, `tooltip` e `icon` en `Setup.DesktopMenuItem`. El icon propio se marca
con `builtin_icon = false`; si no hay, se usa `applications-games` con `builtin_icon = true`.

`bytes` se calcula con el tamaño real de `data/`, que es lo que MojoSetup usa para
pedir espacio y validar el destino.

## Licencia

MojoSetup es zlib (Ryan C. Gordon), compatible con la GPLv2 del proyecto. El commit
vendorizado está fijado en `scripts/build_mojosetup.sh` para reproducibilidad.

## Interfaces (GUI) disponibles

`scripts/build_mojosetup.sh --gui`:

| Modo | Resultado |
| --- | --- |
| `stdio` (por defecto) | Solo texto, sin dependencias de GUI. **Recomendado.** |
| `ncurses` | Interfaz de terminal, enlazada estática |
| `gtk3` | Ventana GTK3, requiere `libgtk-3-dev` al compilar |

Los plugins dinámicos se vendorizan en `data/vendor/mojosetup/guis/<arquitectura>/` y
se empaquetan en la **raíz** del instalador (`guis/`), nunca en `data/`: si se
colocaran en `data/` MojoSetup los instalaría dentro de la carpeta del usuario.

> **No empaquetes Gtk3 por defecto.** El plugin dinámico `libmojosetupgui_gtkplus3.so`
> hace que MojoSetup entre en `PANIC: BUG: fatal() called more than once!` y se quede
> colgado en pantalla azul si GTK no inicializa (sin `DISPLAY`, o sin libgtk en el
> equipo destino). Es un fallo del upstream, no de la app. Por eso `--gui all` lo
> excluye y solo se activa con `--gui gtk3`, avisando. Si ves ese panic, recompila
> sin Gtk3: `scripts/build_mojosetup.sh --gui stdio` y borra
> `data/vendor/mojosetup/guis/`.

El instalador elige la mejor interfaz disponible. Para fijarla:

```bash
MOJOSETUP_UI=stdio   ./juego-instalador.bin     # texto (recomendado)
MOJOSETUP_UI=ncurses ./juego-instalador.bin     # terminal
MOJOSETUP_UI=gtk3    ./juego-instalador.bin     # ventana (solo si se compiló con --gui gtk3)
```

En CI o sobre un tty sin display, usa `MOJOSETUP_UI=stdio`; un plugin GTK sin
`DISPLAY` se queda esperando.

## ARM64

Requiere toolchain cruzado:

```bash
sudo apt install gcc-aarch64-linux-gnu libc6-dev-arm64-cross
scripts/build_mojosetup_arm64.sh          # usa aarch64-linux-gnu-gcc
```

Deja los binarios en `data/vendor/mojosetup-arm64/`. La app usa
`data/vendor/mojosetup/` para el host, así que este directorio sirve para preparar
un paquete destinado a ARM64.

## Progreso durante la instalación

El botón **Probar instalación** de la pestaña MojoSetup ejecuta el instalador
generado y muestra el progreso real, el archivo en curso y la fase:

```text
Instalando archivos · game/sub/archivo.dat
```

MojoSetup emite `archivo: N% (total progress: M%)` y solo escribe si detecta un
terminal (`isatty`). Por eso `src/gui/mojo_install_worker.py` levanta un
pseudo-terminal con `pty` en vez de depender de `script(1)`. Fases detectadas:
`extract` → `metadata` → `done`.

## Limitaciones

- Cada artefacto es específico de arquitectura; no hay un instalador multi-arch.
- El runtime MojoSetup necesita tty; el worker lo resuelve con `pty`.
- Los plugins GTK enlazan contra GTK del sistema destino (no va estático).
- Si el destino ya tiene el juego instalado, MojoSetup omite la copia y la barra
  no avanza: es su comportamiento, no un fallo de la app.