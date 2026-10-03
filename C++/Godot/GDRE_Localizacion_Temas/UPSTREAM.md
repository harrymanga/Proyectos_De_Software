# Upstream fijado

- Proyecto: Godot RE Tools (GDRETools/gdsdecomp)
- Versión: v2.6.4 (ruta fuente antigua `/home/handerson/Descargas/Test/GDRE_Tools_v2.6.4` ya no válida; copia sibling local `../GDRE_tools-v2.6.4-linux/` es binaria+PCK, no árbol fuente)
- Rama/fork de Godot requerido: `nikitalita/godot @ gdre-wb-f964fa714f5` (ver README upstream, sección Requirements)
- Archivos clave del overlay:
  - UI: `standalone/gdre_main.gd`, `standalone/*.tscn`, `standalone/gdre_*.gd`
  - Tema: `standalone/gdre_theme.tres`
  - Registro: `register_types.cpp`, `main/gdre_main_loop.h`

Regla: el upstream **no se edita a mano**. Todo cambio propio vive en este
proyecto y se aplica con `scripts/aplicar_overlay.sh`. Ante una nueva
versión, seguir `docs/ACTUALIZACIONES.md`.
