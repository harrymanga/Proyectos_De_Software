# Herramientas vendorizadas (offline)

Binarios oficiales para builds **sin red** (x86_64):

- `linuxdeploy-x86_64.AppImage` — https://github.com/linuxdeploy/linuxdeploy
- `appimagetool-x86_64.AppImage` — https://github.com/AppImage/AppImageKit

Uso:

```bash
# CLI
appimage-builder build -p ./MiApp \
  --linuxdeploy ./tools/linuxdeploy-x86_64.AppImage \
  --appimagetool ./tools/appimagetool-x86_64.AppImage

# TOML
[tool.appimage-builder.runtime]
linuxdeploy_path = "tools/linuxdeploy-x86_64.AppImage"
appimagetool_path = "tools/appimagetool-x86_64.AppImage"
```

En la GUI: paso 5 → *Actualización y entorno* → rutas locales. Sin estas
rutas se usa `~/.cache/appimage-builder/tools/` y, si falta, se descarga.
