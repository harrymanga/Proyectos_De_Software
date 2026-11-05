"""Definición de la API de Factorio para autocompletado y sintaxis.

Contiene definiciones de funciones, eventos, tipos y eventos del juego
Factorio para proporcionar autocompletado y verificación de sintaxis
en el editor Lua.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LuaFunction:
    """Definición de una función de la API de Factorio."""
    name: str
    parameters: list[str] = field(default_factory=list)
    return_type: str = "nil"
    description: str = ""
    module: str = ""


@dataclass
class LuaEvent:
    """Definición de un evento de Factorio."""
    name: str
    description: str = ""
    parameters: list[str] = field(default_factory=list)


@dataclass
class LuaType:
    """Definición de un tipo de dato de Factorio."""
    name: str
    fields: dict[str, str] = field(default_factory=dict)
    methods: list[str] = field(default_factory=list)


# ============================================================================
# FUNCIONES DE LA API DE FACTORIO
# ============================================================================

FACTORIO_FUNCTIONS: dict[str, LuaFunction] = {}

# --- data (definiciones de prototipos) ---
FACTORIO_FUNCTIONS.update({
    "data.raw": LuaFunction("data.raw", [], "table", "Tabla de prototipos del juego", "data"),
    "data.extend": LuaFunction("data.extend", ["table"], "void", "Agrega prototipos al juego", "data"),
    "data.raw.item": LuaFunction("data.raw.item", [], "table", "Ítem de mods", "data"),
    "data.raw.entity": LuaFunction("data.raw.entity", [], "table", "Entidades del juego", "data"),
    "data.raw.recipe": LuaFunction("data.raw.recipe", [], "table", "Recetas de crafting", "data"),
    "data.raw.technology": LuaFunction("data.raw.technology", [], "table", "Tecnologías de investigación", "data"),
    "data.raw.fluid": LuaFunction("data.raw.fluid", [], "table", "Fluidos del juego", "data"),
    "data.raw.tile": LuaFunction("data.raw.tile", [], "table", "Tejas del terreno", "data"),
})

# ============================================================================
# EVENTOS DE FACTORIO
# ============================================================================

FACTORIO_EVENTS: dict[str, LuaEvent] = {}

FACTORIO_EVENTS.update({
    "on_init": LuaEvent("on_init", "Ejecutado al iniciar el mod por primera vez", []),
    "on_load": LuaEvent("on_load", "Ejecutado al cargar un guardado", []),
    "on_configuration_changed": LuaEvent("on_configuration_changed", "Ejecutado al cambiar la configuración de mods", []),
    "on_player_created": LuaEvent("on_player_created", "Ejecutado cuando un jugador es creado", ["event"]),
    "on_built_entity": LuaEvent("on_built_entity", "Ejecutado cuando se construye una entidad", ["event"]),
    "on_player_mined_entity": LuaEvent("on_player_mined_entity", "Ejecutado cuando un jugador mina una entidad", ["event"]),
    "on_robot_built_entity": LuaEvent("on_robot_built_entity", "Ejecutado cuando un robot construye una entidad", ["event"]),
    "on_robot_mined_entity": LuaEvent("on_robot_mined_entity", "Ejecutado cuando un robot mina una entidad", ["event"]),
    "on_tick": LuaEvent("on_tick", "Ejecutado en cada tick del juego", ["event"]),
    "on_gui_click": LuaEvent("on_gui_click", "Ejecutado cuando se hace clic en un elemento GUI", ["event"]),
    "on_gui_text_changed": LuaEvent("on_gui_text_changed", "Ejecutado cuando cambia el texto de un campo", ["event"]),
    "on_robot_built": LuaEvent("on_robot_built", "Ejecutado cuando un robot construye algo", ["event"]),
    "on_robot_mined": LuaEvent("on_robot_mined", "Ejecutado cuando un robot mina algo", ["event"]),
    "on_player_built_entity": LuaEvent("on_player_built_entity", "Ejecutado cuando un jugador construye una entidad", ["event"]),
})

# ============================================================================
# TIPOS DE DATOS DE FACTORIO
# ============================================================================

FACTORIO_TYPES: dict[str, LuaType] = {}

FACTORIO_TYPES.update({
    "LuaEntity": LuaType("LuaEntity", {
        "name": "string",
        "position": "table",
        "surface": "LuaSurface",
        "force": "LuaForce",
        "health": "number",
        "max_health": "number",
    }, ["destroy", "set_recipe", "get_recipe", "activate"]),
    "LuaPlayer": LuaType("LuaPlayer", {
        "name": "string",
        "position": "table",
        "inventory": "LuaInventory",
        "character": "LuaEntity",
    }, ["print", "insert", "remove_item", "teleport"]),
    "LuaSurface": LuaType("LuaSurface", {
        "name": "string",
        "daytime": "number",
    }, ["create_entity", "find_entities", "create_item"]),
    "LuaForce": LuaType("LuaForce", {
        "name": "string",
        "research_queue": "table",
    }, ["research_technology", "reset_technology_effects"]),
    "LuaInventory": LuaType("LuaInventory", {
        "bar": "number",
        "main": "number",
    }, ["insert", "remove_item", "get_item_count", "is_empty"]),
    "LuaRecipe": LuaType("LuaRecipe", {
        "name": "string",
        "enabled": "boolean",
        "energy_required": "number",
    }, ["set_recipe", "get_ingredients", "get_results"]),
    "LuaItemStack": LuaType("LuaItemStack", {
        "name": "string",
        "count": "number",
        "quality": "number",
    }, ["set_stack", "clear", "transfer_to"]),
})

# ============================================================================
# FUNCIONES GLOBALES DE LUA
# ============================================================================

LUA_GLOBAL_FUNCTIONS = [
    "print", "error", "pcall", "xpcall", "assert", "select",
    "type", "tostring", "tonumber", "pairs", "ipairs",
    "next", "getmetatable", "setmetatable", "rawset", "rawget",
    "collectgarbage", "dofile", "require", "loadfile", "loadstring",
    "math.abs", "math.acos", "math.asin", "math.atan", "math.ceil",
    "math.cos", "math.deg", "math.exp", "math.floor", "math.log",
    "math.max", "math.min", "math.mod", "math.rad", "math.sin",
    "math.sqrt", "math.tan", "math.random", "math.randomseed",
    "string.byte", "string.char", "string.dump", "string.find",
    "string.format", "string.len", "string.lower", "string.match",
    "string.rep", "string.reverse", "string.sub", "string.upper",
    "table.insert", "table.remove", "table.concat", "table.maxn",
    "table.getn", "table.sort",
]

# ============================================================================
# FUNCIONES DE ACCESO API
# ============================================================================

FACTORIO_API_FUNCTIONS = {
    # data
    "data.raw": "Accede a prototipos del juego",
    "data.extend": "Agrega prototipos nuevos",
    # game
    "game.print": "Imprime mensaje en consola del juego",
    "game.create_player": "Crea un nuevo jugador",
    "game.get_player": "Obtiene un jugador por índice",
    "game.surfaces": "Obtiene lista de superficies",
    # game.event
    "game.event.register": "Registra un manejador de evento",
    "game.event.dispatch": "Despacha un evento",
    # game.mods
    "game.mods.list": "Lista mods instalados",
    "game.mods.enable": "Habilita un mod",
    "game.mods.disable": "Deshabilita un mod",
}

# ============================================================================
# FUNCIONES DE UTILIDAD PARA COMPLETADO
# ============================================================================

def get_all_function_names() -> list[str]:
    """Devuelve todos los nombres de funciones disponibles."""
    result = list(FACTORIO_FUNCTIONS)
    result.extend(LUA_GLOBAL_FUNCTIONS)
    result.extend(FACTORIO_API_FUNCTIONS.keys())
    return result


def get_all_event_names() -> list[str]:
    """Devuelve todos los nombres de eventos."""
    return list(FACTORIO_EVENTS.keys())


def get_function_metadata(name: str) -> LuaFunction | None:
    """Devuelve metadatos de una función."""
    return FACTORIO_FUNCTIONS.get(name) or FACTORIO_API_FUNCTIONS.get(name)


def get_event_metadata(name: str) -> LuaEvent | None:
    """Devuelve metadatos de un evento."""
    return FACTORIO_EVENTS.get(name)


def get_type_metadata(name: str) -> LuaType | None:
    """Devuelve metadatos de un tipo."""
    return FACTORIO_TYPES.get(name)


def get_prefix_matches(prefix: str, max_results: int = 50) -> list[str]:
    """Devuelve coincidencias de prefijo para autocompletado."""
    prefix = prefix.lower()
    matches = []
    for name in get_all_function_names():
        if name.lower().startswith(prefix):
            matches.append(name)
        if len(matches) >= max_results:
            break
    return matches


def get_event_matches(prefix: str) -> list[str]:
    """Devuelve coincidencias de eventos por prefijo."""
    prefix = prefix.lower()
    matches = []
    for name in FACTORIO_EVENTS:
        if name.lower().startswith(prefix):
            matches.append(name)
    return matches


def get_type_matches(prefix: str) -> list[str]:
    """Devuelve coincidencias de tipos por prefijo."""
    prefix = prefix.lower()
    matches = []
    for name in FACTORIO_TYPES:
        if name.lower().startswith(prefix):
            matches.append(name)
    return matches