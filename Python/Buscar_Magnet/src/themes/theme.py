"""Temas explícitos claro/oscuro para widgets tkinter."""

THEMES = {
    "light": {"bg": "#f0f0f0", "fg": "#1a1a1a", "entry": "#ffffff",
              "sel": "#2f81f7", "btn": "#ffffff"},
    "dark": {"bg": "#2b2b2b", "fg": "#e0e0e0", "entry": "#3a3a3a",
             "sel": "#4a7ebb", "btn": "#3d3d3d"},
}


def apply_theme(root, dark, widgets, style=None):
    """Aplica el tema a la raíz y a los widgets con fondo propio.

    widgets: dict con claves log/list/status (widgets con configure()).
    style: objeto ttk.Style opcional (widgets ttk); si se omite, solo tk.
    """
    th = THEMES["dark" if dark else "light"]
    root.configure(bg=th["bg"])
    widgets["log"].configure(bg=th["entry"], fg=th["fg"])
    widgets["list"].configure(bg=th["entry"], fg=th["fg"],
                              selectbackground=th["sel"])
    widgets["status"].configure(bg=th["bg"], fg=th["fg"])
    if style is not None:
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", background=th["btn"], foreground=th["fg"])
        style.configure("TEntry", fieldbackground=th["entry"], foreground=th["fg"])
        style.configure("TCombobox", fieldbackground=th["entry"], foreground=th["fg"])
        style.configure("TFrame", background=th["bg"])
        style.configure("TLabel", background=th["bg"], foreground=th["fg"])
    return th
