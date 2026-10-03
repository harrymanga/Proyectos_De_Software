"""Extrae cadenas UI candidatas a traducción desde el upstream GDRE.

Busca literales en popup_error_box("..."), títulos de menús/ventanas y
textos de .tscn. Genera CSV: clave,fuente_en,es (vacío).
Solo stdlib. No modifica el upstream.
"""
import argparse
import csv
import re
from pathlib import Path

GD_PATTERNS = [
    re.compile(r'popup_error_box\(\s*"((?:[^"\\]|\\.)+)"'),
    re.compile(r'\btext\s*=\s*"((?:[^"\\]|\\.)+)"'),
    re.compile(r'\btitle\s*=\s*"((?:[^"\\]|\\.)+)"'),
    re.compile(r'\btooltip_text\s*=\s*"((?:[^"\\]|\\.)+)"'),
]
TSCN_PATTERNS = [
    re.compile(r'^\s*text\s*=\s*"((?:[^"\\]|\\.)+)"', re.M),
    re.compile(r'^\s*title\s*=\s*"((?:[^"\\]|\\.)+)"', re.M),
    re.compile(r'^\s*tooltip_text\s*=\s*"((?:[^"\\]|\\.)+)"', re.M),
    re.compile(r'popup/item_\d+/text\s*=\s*"((?:[^"\\]|\\.)+)"'),
]


def collect(root: Path):
    seen = {}
    for path in sorted((root / "standalone").rglob("*.gd")):
        if "test" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for rx in GD_PATTERNS:
            for m in rx.finditer(text):
                s = m.group(1).strip()
                if len(s) >= 3 and any(c.isalpha() for c in s) and len(s) <= 300:
                    seen.setdefault(s, f"gd:{path.name}")
    for path in sorted((root / "standalone").rglob("*.tscn")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for rx in TSCN_PATTERNS:
            for m in rx.finditer(text):
                s = m.group(1).strip()
                if len(s) >= 3 and any(c.isalpha() for c in s) and len(s) <= 300:
                    seen.setdefault(s, f"tscn:{path.name}")
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extrae cadenas UI a CSV.")
    ap.add_argument("--upstream", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    data = collect(Path(args.upstream))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clave", "fuente_en", "es"])
        for i, (src, origin) in enumerate(sorted(data.items()), 1):
            w.writerow([f"ui_{i:04d}", src, ""])
    print(f"cadenas: {len(data)} -> {out}")


if __name__ == "__main__":
    main()
