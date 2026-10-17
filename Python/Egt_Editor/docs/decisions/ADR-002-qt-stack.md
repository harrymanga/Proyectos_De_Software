# ADR-002 — Stack GUI PySide6

## Contexto

Usuario exige Python + Qt. Guia §58: congelar stack, temas explicitos, hilos para I/O.

## Decisión

PySide6 (LGPL) + `cryptography`. Estructura `src/gui/` unica con GUI, `src/core/` sin Qt, `src/lang/` carga dinamica.

## Consecuencias

`run.sh` crea `.venv` e instala. Temas claro/oscuro explicitos, `QSettings` para tema/idioma.

## Estado

Aceptado.
