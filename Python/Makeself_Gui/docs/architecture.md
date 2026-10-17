# Arquitectura

```text
src/app.py -> src/gui/main_window.py (widgets, menús, statusbar)
  -> src/gui/workers.py (QThread: Create/Info/Extract/Check)
  -> src/core/{builder,validator,inspector,project,runner,deps} (sin Qt)
  -> src/i18n.py + src/lang/lang_xx.json
  -> src/themes/{light,dark}.qss
```

Reglas: ningún widget fuera de `src/gui/`; `src/core/` testeable sin display; I/O largo siempre en hilos; secretos nunca en logs.
