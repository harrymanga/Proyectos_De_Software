# Iconos de TraductorPro

- `traductorpro.svg` — fuente vectorial (edítala aquí y regenera).
- `traductorpro.png` — 256×256 RGBA (generado con `rsvg-convert`).
- `traductorpro.ico` — multi-tamaño 16–256 (generado con PIL).

Regenerar:

```bash
rsvg-convert -w 256 -h 256 traductorpro.svg -o traductorpro.png
python3 -c "from PIL import Image; Image.open('traductorpro.png').convert('RGBA').save('traductorpro.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
```

## AppImage

Para empaquetar con `appimage-builder` (`Proyectos_De_Software/Python/Crear_AppImage`,
`./run.sh`): usa `traductorpro.png` como `--icon` y genera el `.desktop`
apuntando a `main.py` (vía `run.sh` o entry `traductorpro` si se define
console-script en `pyproject.toml`).
