# Actualizaciones del upstream (procedimiento)

El overlay está diseñado para que una versión nueva de GDRE **no** obligue
a rehacer el trabajo a mano:

1. **Fijar la nueva versión**: descargar el nuevo árbol y anotarlo en
   `UPSTREAM.md` (versión + fecha + ruta).
2. **Detectar cambios de UI**:
   `bash scripts/verificar_actualizacion.sh --actual <VIEJO> --nuevo <NUEVO>`
3. **Re-extraer cadenas**:
   `python3 tools/extraer_cadenas.py --upstream <NUEVO> --out locale/plantilla_nueva.csv`
   y fusionar con `locale/es.csv` (conservar traducciones existentes por `clave`;
   las claves nuevas quedan con `es` vacío).
4. **Regenerar tema claro**:
   `python3 themes/generar_tema_claro.py --tema <NUEVO>/standalone/gdre_theme.tres --out themes/gdre_theme_light.tres`.
   Si reporta "Sin reemplazos", el tema base cambió: actualizar `MAP` con los
   nuevos fondos oscuros (verificados en el `.tres`).
5. **Aplicar** sobre copia de trabajo:
   `bash scripts/aplicar_overlay.sh --upstream <NUEVO> --destino /tmp/gdre_overlay_test`
6. La integración en el motor (TranslationServer + conmutador) vive en el fork;
   este overlay solo provee datos + herramientas, por eso sobrevive versiones.

## Integración aplicada (v2.6.4, copia sibling `../GDRE_tools-v2.6.4-linux/`; antes `/home/handerson/godot/modules/gdsdecomp`)

- `standalone/gdre_i18n.gd`: nodo `GDREI18n` (CSV→dict, `traducir()`, temas, prefs).
- `standalone/gdre_main.gd`: `_configurar_i18n()` en `_ready` + items 100/101
  (Idioma es/en, Tema claro/oscuro) en REToolsMenu.
- `standalone/locale/overlay/es.csv` + `standalone/gdre_theme_light.tres`.
- Validado con `--check-only`: sin errores nuevos (3 preexistentes de contexto).
