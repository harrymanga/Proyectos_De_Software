# Changelog

## [0.1.0] - 2026-10-24

### Añadido

- Estructura inicial del proyecto `Mod_Maker`.
- Núcleo multiplataforma: configuración (TOML), internacionalización (es/en), logging, seguridad.
- Plugin de Factorio: extraer, reconstruir, validar y leer metadatos de mods `.zip` con `info.json`.
- Interfaz gráfica base con PySide6: menús (Archivo, Juegos, Mods, Configuración, Ayuda), temas claro/oscuro explícitos, barra de estado.
- Lanzadores `run.sh` y `run.bat` para arranque sin fricción.
- Pruebas unitarias y de integración (config, i18n, seguridad, metadatos, plugin de Factorio).
- Documentación: README operativo, CHANGELOG, plantillas de ADR.
