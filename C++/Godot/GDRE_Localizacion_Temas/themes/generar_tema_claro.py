"""Genera un tema claro a partir de gdre_theme.tres (oscuro) por mapeo explícito.

Solo transforma colores de fondo conocidos; el resto se conserva.
Uso:
  python3 generar_tema_claro.py --tema <gdre_theme.tres> --out <gdre_theme_light.tres>
"""
import argparse
import re
from pathlib import Path

# Mapeo verificado contra gdre_theme.tres (fondos oscuros -> claros).
MAP = {
    "Color(0.147059, 0.173529, 0.232353, 1)": "Color(0.93, 0.93, 0.94, 1)",
    "Color(0.122549, 0.144608, 0.193627, 1)": "Color(0.85, 0.86, 0.88, 1)",
    "Color(0.176471, 0.208235, 0.278824, 1)": "Color(0.88, 0.89, 0.91, 1)",
    "Color(0.196078, 0.231373, 0.309804, 1)": "Color(0.83, 0.84, 0.87, 1)",
    "Color(0.0965684, 0.120984, 0.166773, 1)": "Color(0.9, 0.9, 0.92, 1)",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    text = Path(args.tema).read_text(encoding="utf-8")
    count = 0
    for old, new in MAP.items():
        n = text.count(old)
        text = text.replace(old, new)
        count += n
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Sin uid: el editor asigna uno nuevo al importar (evita "Duplicate UID").
    text = re.sub(r' uid="uid://[a-z0-9]+"', "", text, count=1)
    out.write_text(text, encoding="utf-8")
    print(f"reemplazos: {count} -> {out}")
    if count == 0:
        raise SystemExit("Sin reemplazos: el tema base cambió; revisar MAP.")


if __name__ == "__main__":
    main()
