"""CLI para MOD MAKER - Herramienta de línea de comandos tipo fmtk.

Permite crear, editar, empaquetar, instalar y gestionar mods de Factorio
desde la línea de comandos sin necesidad de la interfaz gráfica.

Comandos:
    create     - Crear un mod nuevo
    extract    - Extraer un mod a una carpeta
    rebuild    - Reconstruir un mod desde una carpeta
    install    - Instalar un mod en la carpeta de mods del juego
    uninstall  - Desinstalar un mod de la carpeta de mods del juego
    list       - Listar mods instalados
    info       - Mostrar información de un mod
    debug      - Gestionar sesiones de depuración Lua
    variables  - Gestionar variables de depuración
    breakpoints - Gestionar puntos de interrupción

Uso:
    mod-maker-<juego> create <name> [--version X.Y.Z] [--author Name] [--desc Text] [--game-version X.Y] [--output /path]
    mod-maker-<juego> extract <mod.zip> [--output /path]
    mod-maker-<juego> rebuild <folder_mod> [--output output.zip]
    mod-maker-<juego> install <mod.zip>
    mod-maker-<juego> uninstall <mod_name>
    mod-maker-<juego> list
    mod-maker-<juego> info <mod.zip>
    mod-maker-<juego> debug start <mod.zip|carpeta>
    mod-maker-<juego> debug pause <session_id>
    mod-maker-<juego> debug resume <session_id>
    mod-maker-<juego> debug stop <session_id>
    mod-maker-<juego> debug list
    mod-maker-<juego> variables set <session_id> <nombre> <valor>
    mod-maker-<juego> variables get <session_id> <nombre>
    mod-maker-<juego> variables list <session_id>
    mod-maker-<juego> variables remove <session_id> <nombre>
    mod-maker-<juego> breakpoints add <session_id> <archivo.lua> <linea>
    mod-maker-<juego> breakpoints remove <session_id> <archivo.lua> <linea>
    mod-maker-<juego> breakpoints list <session_id>

Ejemplos:
    mod-maker-factorio create MiMod --version 1.0.0 --author "Mi Nombre"
    mod-maker-factorio extract MiMod_1.0.0.zip --output ./mi_mod/
    mod-maker-factorio rebuild ./MiMod/
    mod-maker-factorio install MiMod_1.0.0.zip
    mod-maker-factorio list
    mod-maker-factorio info MiMod_1.0.0.zip
    mod-maker-factorio debug start MiMod_1.0.0.zip
    mod-maker-factorio debug list
    mod-maker-factorio variables set abc123 mi_variable 42
    mod-maker-factorio breakpoints add abc123 data.lua 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from src.core.factorio_mod import ModValidationError
from src.core.mod_packager import build_mod_zip
from src.core.plugin_system import PluginSystem
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

try:
    from pyfiglet import Figlet
    HAS_FIGLET = True
except ImportError:
    HAS_FIGLET = False

console = Console()

# ============================================================================
# Constantes de estilo para mensajes de salida (usando rich para colores)
# ============================================================================

OK = "[green]✓[/green]"
ERROR = "[red]✗[/red]"
WARNING = "[yellow]⚠[/yellow]"
INFO = "[blue]ℹ[/blue]"
ARROW = "[cyan]→[/cyan]"


def _print_ok(msg: str) -> None:
    console.print(f"{OK} {msg}")


def _print_error(msg: str) -> None:
    console.print(f"{ERROR} {msg}")


def _print_warning(msg: str) -> None:
    console.print(f"{WARNING} {msg}")


def _print_info(msg: str) -> None:
    console.print(f"{INFO} {msg}")


def _print_header(title: str) -> None:
    console.print(f"\n[bold]{title}[/bold]")
    console.print("=" * len(title))


# ============================================================================
# Parser builders
# ============================================================================

def _add_common_output_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o", "--output", default=None,
        help="Archivo o carpeta de salida",
    )


def _create_create_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "create", help="Crear un mod nuevo"
    )
    p.add_argument("name", help="Nombre del mod")
    p.add_argument("-v", "--version", default="1.0.0",
                   help="Versión del mod (por defecto: 1.0.0)")
    p.add_argument("-a", "--author", default="",
                   help="Autor del mod")
    p.add_argument("-d", "--desc", default="",
                   help="Descripción del mod")
    p.add_argument("-f", "--game-version", default="1.1",
                   help="Versión del juego (por defecto: 1.1)")
    p.add_argument("-o", "--output", default=None,
                   help="Carpeta donde crear el mod")


def _create_extract_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "extract", help="Extraer un mod a una carpeta"
    )
    p.add_argument("mod", help="Archivo .zip del mod a extraer")
    p.add_argument("-o", "--output", default=None,
                   help="Carpeta de destino para extraer")


def _create_rebuild_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "rebuild", help="Reconstruir un mod desde una carpeta"
    )
    p.add_argument("folder", help="Carpeta con el mod extraído")
    p.add_argument("-o", "--output", default=None,
                   help="Archivo ZIP de salida")


def _create_install_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "install", help="Instalar un mod en la carpeta de mods del juego"
    )
    p.add_argument("mod", help="Archivo .zip del mod a instalar")


def _create_uninstall_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "uninstall", help="Desinstalar un mod de la carpeta de mods del juego"
    )
    p.add_argument("nombre", help="Nombre del mod a desinstalar")


def _create_list_parser(subparsers) -> None:
    subparsers.add_parser(
        "list", help="Listar mods instalados"
    )


def _create_info_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "info", help="Mostrar información de un mod"
    )
    p.add_argument("mod", help="Archivo .zip del mod")


# ============================================================================
# Debug subcommands
# ============================================================================

def _create_debug_start_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "start", help="Iniciar una sesión de depuración para un mod"
    )
    p.add_argument("mod", help="Archivo .zip o carpeta del mod a depurar")


def _create_debug_pause_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "pause", help="Pausar una sesión de depuración"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")


def _create_debug_resume_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "resume", help="Reanudar una sesión de depuración"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")


def _create_debug_stop_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "stop", help="Detener una sesión de depuración"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")


def _create_debug_list_parser(subparsers) -> None:
    subparsers.add_parser(
        "list", help="Listar sesiones de depuración activas"
    )


def _build_debug_parser(subparsers) -> None:
    debug_parser = subparsers.add_parser(
        "debug", help="Gestionar sesiones de depuración Lua"
    )
    debug_subparsers = debug_parser.add_subparsers(dest="debug_command")
    _create_debug_start_parser(debug_subparsers)
    _create_debug_pause_parser(debug_subparsers)
    _create_debug_resume_parser(debug_subparsers)
    _create_debug_stop_parser(debug_subparsers)
    _create_debug_list_parser(debug_subparsers)


# ============================================================================
# Variables subcommands
# ============================================================================

def _create_variables_set_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "set", help="Establecer una variable en una sesión de depuración"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")
    p.add_argument("nombre", help="Nombre de la variable")
    p.add_argument("valor", help="Valor de la variable")


def _create_variables_get_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "get", help="Obtener el valor de una variable"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")
    p.add_argument("nombre", help="Nombre de la variable")


def _create_variables_list_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "list", help="Listar variables de una sesión"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")


def _create_variables_remove_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "remove", help="Eliminar una variable de una sesión"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")
    p.add_argument("nombre", help="Nombre de la variable")


def _build_variables_parser(subparsers) -> None:
    vars_parser = subparsers.add_parser(
        "variables", help="Gestionar variables de depuración"
    )
    vars_subparsers = vars_parser.add_subparsers(dest="variables_command")
    _create_variables_set_parser(vars_subparsers)
    _create_variables_get_parser(vars_subparsers)
    _create_variables_list_parser(vars_subparsers)
    _create_variables_remove_parser(vars_subparsers)


# ============================================================================
# Breakpoints subcommands
# ============================================================================

def _create_breakpoints_add_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "add", help="Agregar un punto de interrupción"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")
    p.add_argument("file", help="Archivo .lua del breakpoint")
    p.add_argument("line", type=int, help="Número de línea")


def _create_breakpoints_remove_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "remove", help="Eliminar un punto de interrupción"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")
    p.add_argument("file", help="Archivo .lua del breakpoint")
    p.add_argument("line", type=int, help="Número de línea")


def _create_breakpoints_list_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "list", help="Listar puntos de interrupción de una sesión"
    )
    p.add_argument("session_id", help="ID de la sesión de depuración")


def _build_breakpoints_parser(subparsers) -> None:
    bp_parser = subparsers.add_parser(
        "breakpoints", help="Gestionar puntos de interrupción"
    )
    bp_subparsers = bp_parser.add_subparsers(dest="breakpoints_command")
    _create_breakpoints_add_parser(bp_subparsers)
    _create_breakpoints_remove_parser(bp_subparsers)
    _create_breakpoints_list_parser(bp_subparsers)


# ============================================================================
# Main parser
# ============================================================================

def create_parser(juego_id: str) -> argparse.ArgumentParser:
    """Crear el analizador de argumentos de línea de comandos para un juego."""
    parser = argparse.ArgumentParser(
        prog=f"mod-maker-{juego_id}",
        description=(
            f"Herramienta de línea de comandos para crear, editar y gestionar "
            f"mods de {juego_id}"
        ),
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponibles")

    _create_create_parser(subparsers)
    _create_extract_parser(subparsers)
    _create_rebuild_parser(subparsers)
    _create_install_parser(subparsers)
    _create_uninstall_parser(subparsers)
    _create_list_parser(subparsers)
    _create_info_parser(subparsers)
    _build_debug_parser(subparsers)
    _build_variables_parser(subparsers)
    _build_breakpoints_parser(subparsers)

    return parser


# ============================================================================
# Command handlers
# ============================================================================

def cmd_create(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Create a new mod."""
    if plugin is None:
        _print_error("No se encontró el plugin del juego.")
        return 1

    name = args.name
    version = args.version
    author = args.author
    description = args.desc
    game_version = args.game_version

    output_folder = Path(args.output) if args.output else Path.cwd()
    mod_folder = output_folder / name

    # Validar nombre y versión antes de crear cualquier carpeta
    try:
        metadata = plugin.create_info_json(
            name=name,
            version=version,
            author=author,
            description=description,
            factorio_version=game_version,
        )
    except ModValidationError as exc:
        _print_error(str(exc))
        return 1

    if mod_folder.exists():
        _print_error(f"La carpeta '{mod_folder}' ya existe.")
        return 1

    mod_folder.mkdir(parents=True, exist_ok=True)

    plugin.save_info_json(mod_folder, metadata)

    # Crear data.lua vacío
    (mod_folder / "data.lua").write_text(
        f"-- {name} - data.lua\n",
        encoding="utf-8",
    )

    _print_ok(f"Mod '{name}' creado en: {mod_folder}")
    return 0


def cmd_extract(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Extraer un mod a una carpeta."""
    mod_path = Path(args.mod)
    if not mod_path.exists():
        _print_error(f"El archivo '{mod_path}' no existe.")
        return 1

    output_folder = Path(args.output) if args.output else Path.cwd()
    output_folder = output_folder / mod_path.stem
    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        # Barra de progreso para la extracción
        with tqdm(total=100, desc="Extrayendo", unit="%", bar_format="{l_bar}{bar}| {n:.1f}%") as pbar:
            for i in range(0, 101, 10):
                pbar.update(10)
            plugin.extract(mod_path, output_folder)
        _print_ok(f"Mod extraído en: {output_folder}")
        return 0
    except Exception as exc:  # pragma: no cover - defensivo
        _print_error(f"Error extrayendo mod: {exc}")
        return 1


def cmd_rebuild(args: argparse.Namespace) -> int:
    """Reconstruir un mod desde una carpeta."""
    folder = Path(args.folder)
    if not folder.is_dir():
        _print_error(f"La carpeta '{folder}' no existe.")
        return 1

    output_path = Path(args.output) if args.output else folder.parent / f"{folder.name}.zip"

    try:
        build_mod_zip(folder, output_path)
        _print_ok(f"Mod reconstruido en: {output_path}")
        return 0
    except Exception as exc:  # pragma: no cover - defensivo
        _print_error(f"Error reconstruyendo mod: {exc}")
        return 1


def cmd_install(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Instalar un mod en la carpeta de mods del juego."""
    mod_path = Path(args.mod)
    if not mod_path.exists():
        _print_error(f"El archivo '{mod_path}' no existe.")
        return 1

    try:
        plugin.install_mod(mod_path)
        _print_ok(f"Mod instalado: {mod_path.name}")
        return 0
    except Exception as exc:  # pragma: no cover - defensivo
        _print_error(f"Error instalando mod: {exc}")
        return 1


def cmd_uninstall(args: argparse.Namespace, plugin_system: PluginSystem, juego_id: str) -> int:
    """Desinstalar un mod de la carpeta de mods del juego."""
    plugin = plugin_system.get_plugin(juego_id)

    if not plugin:
        _print_error(f"No se encontró el plugin para el juego '{juego_id}'.")
        _print_info(f"Juegos disponibles: {', '.join(plugin_system.list_plugins())}")
        return 1

    try:
        plugin.uninstall_mod(args.nombre)
        _print_ok(f"Mod desinstalado: {args.nombre}")
        return 0
    except Exception as exc:  # pragma: no cover - defensivo
        _print_error(f"Error desinstalando mod: {exc}")
        return 1


def cmd_list(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Listar mods instalados."""
    mods = plugin.list_installed_mods()
    if not mods:
        _print_info("No hay mods instalados.")
        return 0

    _print_header("Mods instalados:")
    table = Table(show_header=True, box=None)
    table.add_column("#", style="bold blue", width=4)
    table.add_column("Nombre", style="white")
    for i, mod_path in enumerate(mods, 1):
        table.add_row(str(i), mod_path.name)
    console.print(table)
    return 0


def cmd_info(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Mostrar información de un mod."""
    mod_path = Path(args.mod)
    if not mod_path.exists():
        _print_error(f"El archivo '{mod_path}' no existe.")
        return 1

    metadatos = plugin.get_metadata(mod_path)
    if not metadatos:
        _print_error("No se pudieron leer los metadatos del mod.")
        return 1

    _print_header(f"Información del mod: {mod_path.name}")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Campo", style="bold blue", width=15)
    table.add_column("Valor", style="white")
    deps = metadatos.get('dependencies', [])
    table.add_row("Nombre", metadatos.get('name', 'N/A'))
    table.add_row("Versión", metadatos.get('version', 'N/A'))
    table.add_row("Autor", metadatos.get('author', 'N/A'))
    table.add_row("Descripción", metadatos.get('description', 'N/A'))
    table.add_row("Versión juego", metadatos.get('factorio_version', metadatos.get('version_juego', 'N/A')))
    table.add_row("Dependencias", ', '.join(deps) if deps else 'Ninguna')
    console.print(table)
    return 0


# ============================================================================
# Debug command handlers
# ============================================================================

def cmd_debug_start(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Iniciar una sesión de depuración."""
    if not plugin.is_debug_supported():
        _print_error("La depuración Lua no está soportada en este sistema.")
        return 1

    mod_path = Path(args.mod)
    if not mod_path.exists():
        _print_error(f"El mod '{mod_path}' no existe.")
        return 1

    session_id = f"debug_{mod_path.name}"
    session = plugin.create_debug_session(session_id, mod_path)
    if session is None:
        _print_error("No se pudo crear la sesión de depuración.")
        return 1

    if plugin.start_debug(session_id):
        _print_ok(f"Sesión iniciada: {session_id}")
        _print_info(f"Mod: {mod_path.name}")
        output = plugin.get_debug_output(session_id)
        if output:
            print("\nSalida de consola:")
            for linea in output:
                print(f"  {linea}")
        return 0
    else:
        _print_error("No se pudo iniciar la depuración.")
        return 1


def cmd_debug_pause(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Pausar una sesión de depuración."""
    if plugin.pause_debug(args.session_id):
        _print_ok(f"Sesión pausada: {args.session_id}")
        return 0
    _print_error(f"No se pudo pausar la sesión: {args.session_id}")
    return 1


def cmd_debug_resume(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Reanudar una sesión de depuración."""
    if plugin.resume_debug(args.session_id):
        _print_ok(f"Sesión reanudada: {args.session_id}")
        return 0
    _print_error(f"No se pudo reanudar la sesión: {args.session_id}")
    return 1


def cmd_debug_stop(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Detener una sesión de depuración."""
    if plugin.stop_debug(args.session_id):
        _print_ok(f"Sesión detenida: {args.session_id}")
        return 0
    _print_error(f"No se pudo detener la sesión: {args.session_id}")
    return 1


def cmd_debug_list(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Listar sesiones de depuración activas."""
    # Nota: el plugin no expone listar sesiones directamente, mostramos info básica
    _print_info("Sesiones de depuración:")
    _print_info("  Usa 'debug stop <session_id>' para detener una sesión.")
    return 0


# ============================================================================
# Variables command handlers
# ============================================================================

def cmd_variables_set(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Establecer una variable en una sesión de depuración."""
    plugin.debug_adapter.set_lua_variable(args.session_id, args.nombre, args.valor)
    _print_ok(f"Variable establecida: {args.nombre} = {args.valor}")
    return 0


def cmd_variables_get(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Obtener el valor de una variable."""
    variables = plugin.get_debug_variables(args.session_id)
    if args.nombre in variables:
        _print_ok(f"{args.nombre} = {variables[args.nombre]}")
        return 0
    _print_error(f"Variable '{args.nombre}' no encontrada en la sesión.")
    return 1


def cmd_variables_list(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Listar variables de una sesión."""
    variables = plugin.get_debug_variables(args.session_id)
    if not variables:
        _print_info("No hay variables definidas.")
        return 0
    _print_header("Variables de depuración:")
    for nombre, valor in sorted(variables.items()):
        print(f"  {ARROW} {nombre} = {valor}")
    return 0


def cmd_variables_remove(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Eliminar una variable de una sesión."""
    plugin.debug_adapter.set_lua_variable(args.session_id, args.nombre, None)
    _print_ok(f"Variable eliminada: {args.nombre}")
    return 0


# ============================================================================
# Breakpoints command handlers
# ============================================================================

def cmd_breakpoints_add(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Agregar un punto de interrupción."""
    if plugin.set_debug_breakpoint(args.session_id, args.file, args.line):
        _print_ok(f"Breakpoint agregado: {args.file}:{args.line}")
        return 0
    _print_error(f"No se pudo agregar el breakpoint en {args.file}:{args.line}")
    return 1


def cmd_breakpoints_remove(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Eliminar un punto de interrupción."""
    if plugin.remove_debug_breakpoint(args.session_id, args.file, args.line):
        _print_ok(f"Breakpoint eliminado: {args.file}:{args.line}")
        return 0
    _print_error(f"No se pudo eliminar el breakpoint en {args.file}:{args.line}")
    return 1


def cmd_breakpoints_list(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    """Listar puntos de interrupción de una sesión."""
    # Obtener breakpoints de la sesión (necesitamos acceder a la sesión)
    # Por ahora mostramos mensaje informativo
    _print_info("Breakpoints de la sesión:")
    _print_info("  Usa 'breakpoints add' para agregar uno nuevo.")
    return 0


# ============================================================================
# Command routing
# ============================================================================

COMMAND_HANDLERS = {
    "create": lambda a, p: cmd_create(a, p),
    "extract": lambda a, p: cmd_extract(a, p),
    "rebuild": lambda a, _: cmd_rebuild(a),
    "install": lambda a, p: cmd_install(a, p),
    "uninstall": lambda a, ps, ji: cmd_uninstall(a, ps, ji),
    "list": lambda a, p: cmd_list(a, p),
    "info": lambda a, p: cmd_info(a, p),
    "debug": lambda a, p: _route_debug(a, p),
    "variables": lambda a, p: _route_variables(a, p),
    "breakpoints": lambda a, p: _route_breakpoints(a, p),
}


def _route_debug(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    sub = args.debug_command
    if sub == "start":
        return cmd_debug_start(args, plugin)
    elif sub == "pause":
        return cmd_debug_pause(args, plugin)
    elif sub == "resume":
        return cmd_debug_resume(args, plugin)
    elif sub == "stop":
        return cmd_debug_stop(args, plugin)
    elif sub == "list":
        return cmd_debug_list(args, plugin)
    _print_error(f"Comando debug desconocido: {sub}")
    return 1


def _route_variables(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    sub = args.variables_command
    if sub == "set":
        return cmd_variables_set(args, plugin)
    elif sub == "get":
        return cmd_variables_get(args, plugin)
    elif sub == "list":
        return cmd_variables_list(args, plugin)
    elif sub == "remove":
        return cmd_variables_remove(args, plugin)
    _print_error(f"Comando variables desconocido: {sub}")
    return 1


def _route_breakpoints(args: argparse.Namespace, plugin: FactorioPlugin) -> int:
    sub = args.breakpoints_command
    if sub == "add":
        return cmd_breakpoints_add(args, plugin)
    elif sub == "remove":
        return cmd_breakpoints_remove(args, plugin)
    elif sub == "list":
        return cmd_breakpoints_list(args, plugin)
    _print_error(f"Comando breakpoints desconocido: {sub}")
    return 1


# ============================================================================
# Menú interactivo (usando questionary)
# ============================================================================

def _interactive_menu(plugin: FactorioPlugin, plugin_system: PluginSystem, game_id: str) -> int:
    """Muestra un menú interactivo para operaciones de mods."""
    if not HAS_QUESTIONARY:
        _print_error("questionary no está instalado. Usa comandos directos.")
        return 1

    while True:
        option = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                questionary.Choice("Crear mod", value="create"),
                questionary.Choice("Extraer mod", value="extract"),
                questionary.Choice("Reconstruir mod", value="rebuild"),
                questionary.Choice("Instalar mod", value="install"),
                questionary.Choice("Listar mods", value="list"),
                questionary.Choice("Info de mod", value="info"),
                questionary.Choice("Depuración (debug)", value="debug"),
                questionary.Choice("Variables", value="variables"),
                questionary.Choice("Breakpoints", value="breakpoints"),
                questionary.Choice("Salir", value="exit"),
            ],
        ).ask()

        if option is None or option == "exit":
            console.print("[yellow]Saliendo...[/yellow]")
            return 0

        # Para comandos que necesitan argumentos, usar input simple
        if option == "create":
            name = questionary.text("Nombre del mod:").ask()
            if name:
                args = argparse.Namespace(
                    nombre=name, version="1.0.0", author="",
                    desc="", game_version="1.1", output=None
                )
                return cmd_create(args, plugin)

        elif option == "list":
            args = argparse.Namespace()
            return cmd_list(args, plugin)

        elif option == "info":
            mod_path = questionary.text("Ruta al archivo .zip:").ask()
            if mod_path:
                args = argparse.Namespace(mod=mod_path)
                return cmd_info(args, plugin)

        elif option == "extract":
            mod_path = questionary.text("Ruta al archivo .zip:").ask()
            if mod_path:
                args = argparse.Namespace(mod=mod_path, output=None)
                return cmd_extract(args, plugin)

        elif option == "rebuild":
            folder = questionary.text("Ruta a la carpeta del mod:").ask()
            if folder:
                args = argparse.Namespace(folder=folder, output=None)
                return cmd_rebuild(args, plugin)

        elif option == "install":
            mod_path = questionary.text("Ruta al archivo .zip:").ask()
            if mod_path:
                args = argparse.Namespace(mod=mod_path)
                return cmd_install(args, plugin)

        elif option == "uninstall":
            name = questionary.text("Nombre del mod:").ask()
            if name:
                args = argparse.Namespace(nombre=name)
                return cmd_uninstall(args, plugin_system, game_id)

        elif option == "debug":
            _print_info("Usa: mod-maker-<juego> debug start <mod>")
        elif option == "variables":
            _print_info("Usa: mod-maker-<juego> variables <set|get|list|remove>")
        elif option == "breakpoints":
            _print_info("Usa: mod-maker-<juego> breakpoints <add|remove|list>")

    return 0

def main(argv: list[str] | None = None) -> int:
    """Punto de entrada principal de la CLI."""
    # Mostrar logo ASCII al iniciar
    if HAS_FIGLET:
        figlet = Figlet(font='slant')
        console.print(figlet.renderText("Mod Maker"), style="bold cyan")
        console.print("[dim]Herramienta para crear, editar y gestionar mods[/dim]\n")
    else:
        console.print("[bold cyan]Mod Maker[/bold cyan] - Herramienta para crear, editar y gestionar mods\n")

    # Obtener todos los plugins disponibles
    plugin_system = PluginSystem()
    available_games = plugin_system.list_plugins()

    if not available_games:
        _print_error("No se encontraron plugins de juegos instalados.")
        return 1

    # El primer argumento debe ser el juego (ej. factorio, unity, unreal)
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        _print_error("Debe especificar el juego como primer argumento.")
        _print_info("Uso: mod-maker <juego> <comando> [opciones]")
        _print_info(f"Juegos disponibles: {', '.join(available_games)}")
        return 1

    game_id = argv[0]

    # Validar que el juego exista
    if game_id not in available_games:
        _print_error(f"El juego '{game_id}' no está instalado.")
        _print_info(f"Juegos disponibles: {', '.join(available_games)}")
        return 1

    # Obtener el plugin del juego seleccionado
    plugin = plugin_system.get_plugin(game_id)

    if plugin is None:
        _print_error(f"No se encontró el plugin para el juego '{game_id}'.")
        return 1

    # El resto de argumentos son para el parser del juego
    command_args = argv[1:]

    # Crear parser específico para el juego
    parser = create_parser(game_id)
    args = parser.parse_args(command_args)

    if not hasattr(args, "comando") or args.comando is None:
        if HAS_QUESTIONARY:
            return _interactive_menu(plugin, plugin_system, game_id)
        parser.print_help()
        return 1

    # Ejecutar el comando
    handler = COMMAND_HANDLERS.get(args.comando)
    if handler is None:
        _print_error(f"Comando desconocido: {args.comando}")
        return 1

    # Algunos comandos necesitan plugin_system y juego_id extra
    if args.comando == "uninstall":
        return handler(args, plugin_system, game_id)

    return handler(args, plugin)


if __name__ == "__main__":
    sys.exit(main())
