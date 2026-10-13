"""
generate_icon.py - Programmatically creates professional application icons (.ico and .png).
"""

import os
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QGuiApplication,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QRadialGradient,
)

def generate_icons():
    # Requires QGuiApplication instance
    app = QGuiApplication.instance() or QGuiApplication([])

    os.makedirs("assets", exist_ok=True)

    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scale = size / 32.0

    # 1. Background Apple HomeKit squircle container
    bg_path = QPainterPath()
    bg_path.addRoundedRect(0, 0, size, size, 56, 56)
    
    grad = QRadialGradient(size * 0.5, size * 0.4, size * 0.7)
    grad.setColorAt(0.0, QColor("#1e222d"))
    grad.setColorAt(1.0, QColor("#0d0e12"))
    painter.setPen(QPen(QColor(255, 255, 255, 30), 2))
    painter.setBrush(QBrush(grad))
    painter.drawPath(bg_path)

    # 2. Ambient Bulb Glow
    glow_grad = QRadialGradient(16 * scale, 12 * scale, 12 * scale)
    glow_grad.setColorAt(0.0, QColor(255, 214, 10, 140))
    glow_grad.setColorAt(0.6, QColor(245, 158, 11, 40))
    glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(glow_grad))
    painter.drawEllipse(QPointF(16 * scale, 12 * scale), 12 * scale, 12 * scale)

    # 3. Bulb Dome
    path = QPainterPath()
    path.moveTo(11 * scale, 18 * scale)
    path.cubicTo(6 * scale, 14 * scale, 7 * scale, 4 * scale, 16 * scale, 4 * scale)
    path.cubicTo(25 * scale, 4 * scale, 26 * scale, 14 * scale, 21 * scale, 18 * scale)
    path.lineTo(20 * scale, 21 * scale)
    path.lineTo(12 * scale, 21 * scale)
    path.closeSubpath()

    bulb_color = QColor("#ffd60a")
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bulb_color))
    painter.drawPath(path)

    # 4. Screw Base
    base_color = QColor("#94a3b8")
    painter.setBrush(QBrush(base_color))
    painter.drawRoundedRect(12 * scale, 21.5 * scale, 8 * scale, 4.5 * scale, 1.5 * scale, 1.5 * scale)

    # 5. Base Contact
    contact_color = QColor("#475569")
    painter.setBrush(QBrush(contact_color))
    painter.drawRoundedRect(14 * scale, 26 * scale, 4 * scale, 2 * scale, 1.0 * scale, 1.0 * scale)

    # 6. Filament
    painter.setPen(QPen(QColor("#ffffff"), 1.4 * scale))
    painter.drawLine(QPointF(14 * scale, 11 * scale), QPointF(16 * scale, 9 * scale))
    painter.drawLine(QPointF(16 * scale, 9 * scale), QPointF(18 * scale, 11 * scale))

    painter.end()

    # Save PNG and ICO
    ico_path = os.path.join("assets", "app_icon.ico")
    png_path = os.path.join("assets", "app_icon.png")

    pixmap.save(png_path, "PNG")
    pixmap.save(ico_path, "ICO")

    print(f"Generated icons successfully:\n - {png_path}\n - {ico_path}")

if __name__ == "__main__":
    generate_icons()
