"""Genera el icono oficial de appimage-builder (solo stdlib + PySide6).

Dibuja: fondo degradado azul redondeado + paquete blanco con cinta +
insignia de descarga. Salida: assets/icon-512.png (+256/128/64/32).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG_TOP = QColor("#2f7ed8")
BG_BOTTOM = QColor("#0d2f5f")
TAPE = QColor("#1e5aa8")
BADGE = QColor("#27ae60")
WHITE = QColor("#ffffff")


def _rounded_rect(x: float, y: float, w: float, h: float, r: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(x, y, w, h, r, r)
    return path


def draw(size: int) -> QImage:
    s = size / 512.0
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Fondo degradado.
    bg = QLinearGradient(0, 0, 0, size)
    bg.setColorAt(0.0, BG_TOP)
    bg.setColorAt(1.0, BG_BOTTOM)
    painter.fillPath(_rounded_rect(8 * s, 8 * s, 496 * s, 496 * s, 112 * s), bg)

    # Paquete blanco.
    painter.fillPath(_rounded_rect(150 * s, 196 * s, 212 * s, 184 * s, 24 * s), WHITE)
    # Cinta vertical.
    painter.fillRect(int(239 * s), int(196 * s), int(34 * s), int(184 * s), TAPE)
    # Solapa superior.
    pen = QPen(TAPE, 14 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(int(150 * s), int(216 * s), int(256 * s), int(262 * s))
    painter.drawLine(int(362 * s), int(216 * s), int(256 * s), int(262 * s))
    painter.setPen(Qt.PenStyle.NoPen)

    # Insignia de descarga.
    painter.setBrush(BADGE)
    painter.drawEllipse(int(302 * s), int(302 * s), int(128 * s), int(128 * s))
    arrow_pen = QPen(WHITE, 30 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    arrow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(arrow_pen)
    painter.drawLine(int(366 * s), int(330 * s), int(366 * s), int(392 * s))
    painter.drawLine(int(366 * s), int(392 * s), int(336 * s), int(362 * s))
    painter.drawLine(int(366 * s), int(392 * s), int(396 * s), int(362 * s))

    painter.end()
    return image


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for size in (512, 256, 128, 64, 32):
        dest = ASSETS / f"icon-{size}.png"
        if not draw(size).save(str(dest)):
            print(f"ERROR escribiendo {dest}", file=sys.stderr)
            return 1
        print(f"OK {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
