# Buscar_Magnet

Búsqueda recursiva de enlaces magnet + verificación de semillas, con GUI tkinter.

## Contenido (`src/` por roles)

- `gui/gui_magnet.py` — solo presentación y eventos.
- `core/workers.py` — búsqueda/verificación en hilo (emite eventos a cola).
- `core/buscar_magnet.py`, `core/asinc.py`, `core/verificar_magnet.py` —
  motores puros (logging + CLI argparse, cero GUI).
- `lang/i18n.py` + `lang/lang_*.json` — textos (agregar idioma = añadir JSON).
- `themes/temas.py` — temas explícitos claro/oscuro.
- `configuracion.py` — persistencia + guardado JSON (transversal).
- `data/` — JSON de resultados.

CLI directo (sin GUI): `python src/core/buscar_magnet.py URL [-d 2]`.

## Uso

```bash
./run.sh        # crea .venv, instala deps y abre la GUI (Linux/macOS)
```

En Windows: `run.bat`. URL + profundidad + motor (sync/async) → Buscar →
Verificar → Guardar JSON. Requiere internet.

> **Verificar** necesita `libtorrent` (opcional, import perezoso: la GUI
> arranca sin él y avisa al usarlo). Actívalo según tu distro:
>
> ```bash
> sudo pacman -S libtorrent-rasterbar   # Arch/Manjaro
> sudo apt install python3-libtorrent   # Debian/Ubuntu
> sudo dnf install python3-libtorrent   # Fedora
> ./run.sh --system   # recrea el venv con paquetes del sistema
> ```

## Entornos virtuales y paquetes del sistema

- `run.sh` crea `.venv` **aislado**: no ve `/usr/lib/python3.x/site-packages`.
- `pip install libtorrent` falla en Python nuevos (sin wheel publicado).
- Por eso los bindings se instalan con el gestor del sistema y el venv
  debe recrearse con acceso a ellos: `./run.sh --system` equivale a
  `python3 -m venv --system-site-packages .venv` (un venv ya creado no
  puede cambiar de modo; hay que recrearlo, el script lo hace solo).
- Sin `--system`, el aislamiento es total (comportamiento por defecto,
  recomendado salvo que necesites un paquete del sistema).
- **Automático**: si `system-packages.txt` lista un módulo importable por el
  python del sistema pero no instalable por pip en el venv, `run.sh` recrea
  solo el venv con `--system-site-packages` (equivale a pasar `--system`).
  `./run.sh --system` lo fuerza manualmente.
