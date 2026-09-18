# Release — appimage-builder

## Versionado

La versión vive en dos sitios que deben ir sincronizados:

- `pyproject.toml` → `project.version` (más `tool.commitizen.version`)
- `src/appimage_builder/__init__.py` → `__version__`

## Publicar

```bash
# 1. Actualizar versión en ambos archivos + CHANGELOG
# 2. Tests + lint en verde
python -m pytest tests/ -m "not slow" -q
ruff check src/ tests/ && ruff format --check src/ tests/
# 3. Tag y push (dispara .github/workflows/release.yml)
git tag v0.2.0 && git push origin v0.2.0
```

El workflow `release.yml` construye sdist/wheel (`python -m build`) y crea el
GitHub Release con las notas generadas automáticamente.

## CI

`ci.yml` (+ `.gitlab-ci.yml` equivalente): lint (ruff) + matriz de tests en
Python 3.11–3.13 sobre Ubuntu (GUI sin X: `QT_QPA_PLATFORM=offscreen`). Los tests marcados
`slow` (requieren red: `pip install` real) no corren en CI; ejecútalos en
local con `python -m pytest tests/ -m slow -q` o vía `tox -e slow`.
