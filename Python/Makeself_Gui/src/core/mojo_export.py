"""Exporta un instalador MojoSetup (evita el staging en /tmp de Makeself).

MojoSetup lee su propio binario como ZIP anexado y escribe directo al destino
elegido por el usuario, por lo que no necesita ~2x de espacio temporal.
Binarios vendorizados en data/vendor/mojosetup (ver scripts/build_mojosetup.sh).
"""
from __future__ import annotations

import os
import shutil
import zipfile
from dataclasses import dataclass, field

VENDOR_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "vendor", "mojosetup",
)
RUNTIME_SCRIPTS = ("mojosetup_init.lua", "mojosetup_mainline.lua", "localization.lua")


class MojoExportError(RuntimeError):
    """Falta un requisito para exportar (binarios, scripts o datos)."""


@dataclass
class MojoSettings:
    vendor: str = "makeself-gui.local"
    package_id: str = "miapp"
    version: str = "1.0"
    description: str = "Mi App"
    destination: str = ""  # vacío = el usuario lo elige en el instalador
    recommended: list[str] = field(default_factory=lambda: ["/opt/games"])
    launcher: str = ""  # relativo al destino, ej. "start.sh"
    desktop_name: str = ""
    genericname: str = ""  # obligatorio en Setup.DesktopMenuItem
    tooltip: str = ""
    icon: str = ""
    eula: str = ""  # ruta a un .txt dentro de archive_dir


def slugify(label: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in label).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "miapp"


def detect_launcher(archive_dir: str) -> str:
    """Ruta relativa del lanzador típico, o "" si no se reconoce.

    `startmojo.sh` queda excluido a propósito: es residuo de un instalador
    MojoSetup previo, no el lanzador del juego.
    """
    for name in ("start.sh", "start.bash", "AppRun", "run.sh", "launch.sh"):
        if os.path.isfile(os.path.join(archive_dir, name)):
            return name
    for dirpath, _dirnames, filenames in os.walk(archive_dir):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.access(full, os.X_OK) and not name.endswith(
                    (".sh", ".bash", ".so", ".dll", ".py", ".desktop")):
                return os.path.relpath(full, archive_dir)
    return ""


def _lua_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_config_lua(settings: MojoSettings, total_bytes: int, with_eula: bool) -> str:
    """Genera scripts/config.lua. Función pura: los tests la validan."""
    lines = [
        "-- Generado por Makeself GUI. Editable a mano si se personaliza.",
        "local TOTAL_INSTALL_SIZE = %d;" % max(total_bytes, 0),
        "",
        "Setup.Package",
        "{",
        "    vendor = %s," % _lua_str(settings.vendor),
        "    id = %s," % _lua_str(settings.package_id),
        "    description = %s," % _lua_str(settings.description),
        "    version = %s," % _lua_str(settings.version),
        "    write_manifest = true,",
        "    support_uninstall = true,",
    ]
    if settings.destination:
        lines.append("    destination = %s," % _lua_str(settings.destination))
    recommended = [d for d in settings.recommended if d]
    if recommended:
        joined = ",\n        ".join(_lua_str(d) for d in recommended)
        lines.append("    recommended_destinations =\n    {\n        %s\n    }," % joined)
    if with_eula:
        lines += [
            "",
            "    Setup.Eula",
            "    {",
            "        description = \"End User License Agreement\",",
            "        source = \"LICENSE.txt\",",
            "    },",
        ]
    lines += [
        "",
        "    Setup.Option",
        "    {",
        "        value = true,",
        "        required = true,",
        "        bytes = TOTAL_INSTALL_SIZE,",
        "        description = %s," % _lua_str(settings.description),
        "",
        "        Setup.File",
        "        {",
        '            wildcards = "*",',
        "        },",
    ]
    if settings.launcher:
        lines += [
            "",
            "        Setup.DesktopMenuItem",
            "            {",
            "                name = %s," % _lua_str(settings.desktop_name or settings.description),
            # genericname es obligatorio: MojoSetup aborta si falta.
            "                genericname = %s," % _lua_str(
                settings.genericname or settings.desktop_name or settings.description),
            "                tooltip = %s," % _lua_str(
                settings.tooltip or settings.description),
        ]
        # MojoSetup exige `icon` explícito; si el usuario no aporta uno se usa
        # un icono estándar del sistema (builtin_icon = true).
        if settings.icon:
            lines.append("                builtin_icon = false,")
            lines.append("                icon = %s," % _lua_str(settings.icon))
        else:
            lines.append("                builtin_icon = true,")
            lines.append('                icon = "applications-games",')
        lines += [
            f'                commandline = "%0/{settings.launcher}",',
            '                workingdir = "%0",',
            "                category = \"Game\",",
            "            },",
        ]
    lines += [
        "    },",
        "}",
        "",
    ]
    return "\n".join(lines)


def vendor_status() -> tuple[bool, str]:
    """(listo, mensaje) para diagnosticar qué falta para exportar."""
    if not os.path.isdir(VENDOR_DIR):
        return False, f"faltan binarios en {VENDOR_DIR} (ejecuta scripts/build_mojosetup.sh)"
    if not os.path.isfile(os.path.join(VENDOR_DIR, "mojosetup")):
        return False, "falta data/vendor/mojosetup/mojosetup"
    missing = [s for s in RUNTIME_SCRIPTS
               if not os.path.isfile(os.path.join(VENDOR_DIR, "scripts", s))]
    if missing:
        return False, "faltan scripts runtime: " + ", ".join(missing)
    return True, "listo"


def _copy_tree(src: str, dst: str, exclude: set[str]) -> None:
    """Copia el contenido de src a dst saltando nombres de exclude."""
    for entry in os.listdir(src):
        if entry in exclude:
            continue
        s = os.path.join(src, entry)
        d = os.path.join(dst, entry)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks=True)
        else:
            shutil.copy2(s, d)


def export_mojosetup(
    archive_dir: str,
    output: str,
    settings: MojoSettings,
    vendor_dir: str = "",
) -> str:
    """Construye el instalador auto-extraíble MojoSetup. Devuelve la ruta final."""
    vendor = vendor_dir or VENDOR_DIR
    if not os.path.isfile(os.path.join(vendor, "mojosetup")):
        raise MojoExportError(
            f"faltan binarios de MojoSetup en {vendor} (ejecuta scripts/build_mojosetup.sh)")
    if not os.path.isdir(archive_dir):
        raise MojoExportError(f"archive_dir no existe: {archive_dir}")
    if os.path.abspath(archive_dir) == os.path.abspath(os.path.dirname(output) or "."):
        raise MojoExportError("el archivo de salida no puede estar dentro de archive_dir")

    stage = output + ".stage"
    shutil.rmtree(stage, ignore_errors=True)
    data_dir = os.path.join(stage, "data")
    scripts_dir = os.path.join(stage, "scripts")
    os.makedirs(data_dir)
    os.makedirs(scripts_dir)

    # Los archivos del usuario van a data/ (payload) y no incluyen el exportador.
    exclude = {"proyecto.msgui.json"}
    if settings.launcher and os.path.isfile(os.path.join(archive_dir, settings.launcher)):
        exclude.add(settings.launcher)
    _copy_tree(archive_dir, data_dir, exclude)

    with_eula = bool(settings.eula) and os.path.isfile(
        os.path.join(archive_dir, os.path.basename(settings.eula)))
    if with_eula:
        shutil.copy2(os.path.join(archive_dir, os.path.basename(settings.eula)),
                     os.path.join(data_dir, "LICENSE.txt"))

    for script in RUNTIME_SCRIPTS:
        shutil.copy2(os.path.join(vendor, "scripts", script),
                     os.path.join(scripts_dir, script))

    # Los plugins GUI van en la raíz del paquete (guis/), no en data/: si no,
    # MojoSetup acabaría instalándolos dentro de la carpeta del usuario.
    _copy_gui_plugins(vendor, stage)

    total = _dir_size(data_dir)
    with open(os.path.join(scripts_dir, "config.lua"), "w", encoding="utf-8") as f:
        f.write(build_config_lua(settings, total, with_eula))

    zip_path = output + ".zip"
    _zip_stage(stage, zip_path)

    final = output
    shutil.copy2(os.path.join(vendor, "mojosetup"), final)
    with open(final, "ab") as out_f, open(zip_path, "rb") as zip_f:
        shutil.copyfileobj(zip_f, out_f, 1024 * 1024)
    os.chmod(final, 0o755)

    shutil.rmtree(stage, ignore_errors=True)
    os.remove(zip_path)
    return final


def plugin_warning(vendor_dir: str = "") -> str:
    """Aviso si hay plugins GUI frágiles empaquetados.

    El plugin Gtk3 hace que MojoSetup entre en PANIC si GTK no inicializa
    (sin DISPLAY o sin libgtk en el equipo destino), dejando el instalador
    colgado. Se recomienda recompilar sin él.
    """
    base = vendor_dir or VENDOR_DIR
    guis = os.path.join(base, "guis")
    if not os.path.isdir(guis):
        return ""
    found = []
    for arch in sorted(os.listdir(guis)):
        arch_dir = os.path.join(guis, arch)
        if not os.path.isdir(arch_dir):
            continue
        for name in sorted(os.listdir(arch_dir)):
            if "gtk" in name.lower():
                found.append(f"{arch}/{name}")
    if not found:
        return ""
    return ("plugin Gtk3 detectado (" + ", ".join(found) + "): puede causar PANIC en "
            "equipos sin Gtk3 o sin pantalla. Recompila con "
            "scripts/build_mojosetup.sh --gui ncurses")


def _copy_gui_plugins(vendor: str, stage: str) -> int:
    """Copia guis/<arquitectura> a la raíz del paquete si hay plugins.

    MojoSetup busca los plugins en <base>/guis/<arch>/. Si el instalador corre
    en otra arquitectura simplemente no los encontrará y usará el GUI embebido
    (stdio/ncurses).
    """
    guis_root = os.path.join(vendor, "guis")
    if not os.path.isdir(guis_root):
        return 0
    copied = 0
    for arch in sorted(os.listdir(guis_root)):
        src = os.path.join(guis_root, arch)
        if not os.path.isdir(src):
            continue
        plugins = [n for n in os.listdir(src) if os.path.isfile(os.path.join(src, n))]
        if not plugins:
            continue
        dst = os.path.join(stage, "guis", arch)
        shutil.copytree(src, dst)
        copied += len(plugins)
    if copied == 0:
        shutil.rmtree(os.path.join(stage, "guis"), ignore_errors=True)
    return copied


def _dir_size(path: str) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for name in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                continue
    return total


def _zip_stage(stage: str, zip_path: str) -> None:
    """Crea el ZIP con rutas relativas (data/, scripts/) como espera MojoSetup."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for dirpath, _dirnames, filenames in os.walk(stage):
            rel_dir = os.path.relpath(dirpath, stage)
            if rel_dir != ".":
                zf.writestr(rel_dir.replace(os.sep, "/") + "/", b"")
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                arc = os.path.join(rel_dir, name).replace(os.sep, "/").lstrip("./")
                zf.write(full, arc)


def vendor_files(vendor_dir: str = "") -> dict:
    """Inventario de lo vendorizado, para diagnóstico y documentación."""
    base = vendor_dir or VENDOR_DIR
    files = {}
    for rel in ("mojosetup", "make_self_extracting"):
        files[rel] = os.path.isfile(os.path.join(base, rel))
    files["scripts"] = {
        s: os.path.isfile(os.path.join(base, "scripts", s)) for s in RUNTIME_SCRIPTS
    }
    return files