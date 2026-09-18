# Changelog

Todos los cambios notables se documentan aquí (formato Keep a Changelog).
El historial detallado vive en `docs/interno/SESSION.md`.

## [0.1.0] - 2025-01-01

### Añadido
- CLI `appimage-builder` (Typer + Rich): `init`, `build`, `validate`, `doctor`.
- Wizard GUI de 7 pasos (PySide6 + MVVM).
- Builders Python / nativos (Rust, Go, CMake, Meson, Make) / binarios precompilados.
- Herramientas vendorizadas offline en `tools/` (linuxdeploy, appimagetool).
- Suite de 67 tests (`unit`, `integration`, `gui`, `slow`).
