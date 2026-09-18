"""Ayuda en español para las opciones integradas de Typer/Click.

Typer genera `--install-completion` / `--show-completion` y Click el `--help`
con textos fijos en inglés que no son configurables. Se ajustan de dos formas
complementarias (duck-typing, sin importar el click vendoreado):

- `patch_typer_defaults()`: reescribe los textos en las factorías de Typer y
  en `Command.get_help_option`; se ejecuta al importar este módulo, por lo que
  cubre `app()`, `CliRunner` y cualquier otro flujo.
- `apply_spanish_help(cmd)`: ajuste directo sobre un comando ya construido.
"""

from __future__ import annotations

_HELP_TEXTS = {
    "--help": "Muestra esta ayuda y sale.",
    "--install-completion": "Instala el autocompletado para el shell actual.",
    "--show-completion": (
        "Muestra el autocompletado para el shell actual, para copiarlo "
        "o personalizar la instalación."
    ),
}


def patch_typer_defaults() -> bool:
    """Parchea las factorías de Typer/Click. Devuelve True si aplicó."""
    applied = False
    try:
        import typer.main as _typer_main

        _orig_arguments = _typer_main.get_install_completion_arguments

        def _es_arguments():  # type: ignore[no-untyped-def]
            install_param, show_param = _orig_arguments()
            install_param.help = _HELP_TEXTS["--install-completion"]
            show_param.help = _HELP_TEXTS["--show-completion"]
            return install_param, show_param

        _typer_main.get_install_completion_arguments = _es_arguments  # type: ignore[method-assign]
        applied = True
    except (ImportError, AttributeError):
        pass
    try:
        from typer import _click as _vendored_click

        _command_cls = _vendored_click.core.Command
        if not getattr(_command_cls, "_spanish_help_patched", False):
            _orig_help_option = _command_cls.get_help_option

            def _es_help_option(self, ctx):  # type: ignore[no-untyped-def]
                option = _orig_help_option(self, ctx)
                if option is not None:
                    option.help = _HELP_TEXTS["--help"]
                return option

            _command_cls.get_help_option = _es_help_option  # type: ignore[method-assign]
            _command_cls._spanish_help_patched = True  # type: ignore[attr-defined]
        applied = True
    except (ImportError, AttributeError):
        pass
    return applied


def apply_spanish_help(cmd: object) -> None:
    """Traduce los help de opciones integradas, recursivo a subcomandos."""
    for param in getattr(cmd, "params", []):
        opts = getattr(param, "opts", []) or []
        for opt in opts:
            if opt in _HELP_TEXTS and getattr(param, "help", None) != _HELP_TEXTS[opt]:
                param.help = _HELP_TEXTS[opt]
    # Click crea --help al vuelo en get_help_option (no está en params).
    get_help_option = getattr(cmd, "get_help_option", None)
    if callable(get_help_option) and not getattr(cmd, "_spanish_help_patched", False):
        try:
            cmd._spanish_help_patched = True  # type: ignore[attr-defined]

            def _wrapper(ctx: object, _orig=get_help_option) -> object:  # type: ignore[no-untyped-def]
                opt = _orig(ctx)
                opt.help = _HELP_TEXTS["--help"]  # type: ignore[attr-defined]
                return opt

            cmd.get_help_option = _wrapper  # type: ignore[attr-defined,method-assign]
        except (AttributeError, TypeError):
            pass
    commands = getattr(cmd, "commands", {}) or {}
    for sub in commands.values():
        apply_spanish_help(sub)


patch_typer_defaults()
