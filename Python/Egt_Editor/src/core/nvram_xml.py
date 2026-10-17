"""Parser NVRAM-XML EGT (§4: formato real verificado en 2 XML de ~750KB).

Formato archivo:
  <?xml version="1.0"?>
  <machine_parameters>...</machine_parameters>
  <nvram>
    <area id="MAIN">...<parameter .../>...</area>
    [<area id="GAMES">...]
    <NVRAMByAttributes>...<parameter .../>...</NVRAMByAttributes>
  </nvram>
  <nvram_CRC CRC="..." />

No es XML de raiz unica: se envuelve en <root> para parsear.
Edicion por reemplazo dirigido + reserializado con ElementTree.
CRC se preserva tal cual (ambos XML de referencia comparten el mismo
CRC pese a valores distintos: no es hash de valores editables).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

PARAM_RE = re.compile(r"<parameter\b[^>]*?/>", re.DOTALL)


@dataclass
class NvramParameter:
    name: str
    address: str
    size: str
    value: str
    section: str  # MAIN / GAMES / BYATTR
    context: str = ""  # grupo/descripcion padre concatenado
    attrs: dict = field(default_factory=dict)


@dataclass
class NvramDocument:
    path: Path
    machine_params: dict
    parameters: list[NvramParameter]
    crc: str = ""
    game_version: str = ""

    def get(self, name: str) -> NvramParameter | None:
        for p in self.parameters:
            if p.name == name:
                return p
        return None

    def set_value(self, name: str, value: str) -> bool:
        p = self.get(name)
        if p is None:
            return False
        p.value = value.strip()
        return True

    def validate(self) -> list[str]:
        """Chequeos sin adivinar CRC: size vs cantidad de bytes en value."""
        errors: list[str] = []
        for p in self.parameters:
            try:
                size = int(p.size)
            except ValueError:
                continue
            if not p.value.strip():
                continue
            parts = p.value.split()
            # value="a b c" o value="15": cuenta tokens; si es un token puede ser escalar.
            if len(parts) > 1 and len(parts) != size:
                errors.append(f"{p.name}: size={size} pero value trae {len(parts)} bytes")
        return errors

    def to_jsonable(self) -> dict:
        return {
            "filename": self.path.name,
            "game_version": self.game_version,
            "crc": self.crc,
            "count": len(self.parameters),
            "parameters": [
                {"name": p.name, "address": p.address, "size": p.size,
                 "value": p.value, "section": p.section, "context": p.context,
                 "attrs": p.attrs}
                for p in self.parameters
            ],
        }


def _wrap(text: str) -> str:
    text = re.sub(r"<\?xml[^?]*\?>", "", text, count=1)
    return f"<root>{text}</root>"


def parse_nvram_xml(path: Path) -> NvramDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    root = ET.fromstring(_wrap(text))
    mp = root.find("machine_parameters")
    machine_params: dict = {}
    game_version = ""
    if mp is not None:
        for child in mp:
            machine_params[child.tag] = dict(child.attrib)
            if child.tag == "game_version" and "parameter" in child.attrib:
                game_version = child.attrib["parameter"]
    nvram = root.find("nvram")
    params: list[NvramParameter] = []
    if nvram is not None:
        for area in nvram.findall("area"):
            sec = area.get("id", "MAIN")
            _collect(area, sec, [], params)
        byattr = nvram.find("NVRAMByAttributes")
        if byattr is not None:
            for el in byattr.findall("parameter"):
                params.append(_to_param(el, "BYATTR", "NVRAMByAttributes"))
    crc_el = root.find("nvram_CRC")
    crc = crc_el.get("CRC", "") if crc_el is not None else ""
    return NvramDocument(path, machine_params, params, crc, game_version)


def _collect(elem: ET.Element, section: str, ctx: list[str], out: list[NvramParameter]) -> None:
    for child in elem:
        if child.tag == "parameter":
            out.append(_to_param(child, section, " / ".join(ctx)))
        elif child.tag in ("group", "class"):
            label = child.get("description") or child.get("type") or child.get("nvram_params") or child.tag
            _collect(child, section, ctx + [label], out)
        else:
            _collect(child, section, ctx, out)


def _to_param(el: ET.Element, section: str, context: str) -> NvramParameter:
    a = dict(el.attrib)
    return NvramParameter(
        name=a.get("name", ""),
        address=a.get("address", ""),
        size=a.get("size", ""),
        value=a.get("value", ""),
        section=section,
        context=context,
        attrs={k: v for k, v in a.items() if k not in ("name", "address", "size", "value")},
    )


def serialize(doc: NvramDocument) -> str:
    """Reserializa preservando las 3 secciones de alto nivel."""
    lines = ['<?xml version="1.0"?>', "<machine_parameters>"]
    for tag, attrs in doc.machine_params.items():
        attr_s = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        lines.append(f"\t<{tag} {attr_s} />")
    lines.append("</machine_parameters>")
    lines.append("<nvram>")
    # Reconstruye plano: MAIN, GAMES, BYATTR (se pierde anidado visual,
    # se conserva semantica nombre/address/size/value + contexto en comentario).
    for section in ("MAIN", "GAMES", "BYATTR"):
        items = [p for p in doc.parameters if p.section == section]
        if not items:
            continue
        if section == "BYATTR":
            lines.append("<NVRAMByAttributes>")
        else:
            lines.append(f'\t<area id="{section}">')
        for p in items:
            extra = " ".join(f'{k}="{v}"' for k, v in p.attrs.items())
            extra = f" {extra}" if extra else ""
            lines.append(
                f'\t\t<!-- {p.context} -->' if p.context else ""
            )
            lines.append(
                f'\t\t<parameter name="{p.name}" size="{p.size}"'
                f'{extra} address="{p.address}" value="{p.value}" />'
            )
        lines.append("\t</NVRAMByAttributes>" if section == "BYATTR" else "\t</area>")
    lines.append("</nvram>")
    lines.append(f'<nvram_CRC CRC="{doc.crc}" />')
    lines.append("")
    return "\n".join(l for l in lines if l != "")
