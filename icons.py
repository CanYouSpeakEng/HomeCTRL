"""
icons.py - Pure Vector Icon Engine for HomeCTRL.

Renders 100% custom, mathematical vector icons using QPainter and QPainterPath.
Zero emojis, zero generic raster icons, resolution-independent crisp rendering.
"""

import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter,
    QPainterPath,
    QColor,
    QPen,
    QBrush,
    QPixmap,
    QIcon,
)


def draw_power_icon(painter: QPainter, rect: QRectF, color: QColor, stroke_width: float = 2.4):
    """Draws Apple-style power symbol: open circle arc + vertical notch line."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    cx = rect.center().x()
    cy = rect.center().y()
    r = min(rect.width(), rect.height()) * 0.38

    # 1. Circle Arc (from 135 deg to 45 deg, opening at top 90 deg)
    arc_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
    # in Qt degrees: 90 is 12 o'clock, but QPainter.drawArc uses 1/16th of a degree counterclockwise from 3 o'clock (0 deg)
    # Top is 90 deg. We want arc from 130 deg to 50 deg (sweep of -280 deg)
    start_angle = int(130 * 16)
    span_angle = int(-260 * 16)
    painter.drawArc(arc_rect, start_angle, span_angle)

    # 2. Vertical line at top
    line_top = cy - r * 1.15
    line_bottom = cy - r * 0.15
    painter.drawLine(QPointF(cx, line_top), QPointF(cx, line_bottom))
    painter.restore()


def draw_brightness_icon(painter: QPainter, rect: QRectF, color: QColor, stroke_width: float = 1.8):
    """Draws modern minimalist Sun vector: center circle + 8 radiant rays."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    cx = rect.center().x()
    cy = rect.center().y()
    size = min(rect.width(), rect.height())
    r_core = size * 0.18
    r_ray_inner = size * 0.28
    r_ray_outer = size * 0.40

    # Center circle
    painter.setBrush(QBrush(color))
    painter.drawEllipse(QPointF(cx, cy), r_core, r_core)

    # 8 Rays
    for i in range(8):
        angle = i * (math.pi / 4.0)
        x1 = cx + math.cos(angle) * r_ray_inner
        y1 = cy + math.sin(angle) * r_ray_inner
        x2 = cx + math.cos(angle) * r_ray_outer
        y2 = cy + math.sin(angle) * r_ray_outer
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def draw_temperature_icon(painter: QPainter, rect: QRectF, color: QColor, stroke_width: float = 1.8):
    """Draws sleek Kelvin temperature thermometer vector."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    cx = rect.center().x()
    cy = rect.center().y()
    size = min(rect.width(), rect.height())

    # Thermometer stem
    stem_w = size * 0.14
    stem_top = cy - size * 0.38
    stem_bottom = cy + size * 0.12

    path = QPainterPath()
    path.moveTo(cx - stem_w / 2, stem_bottom)
    path.lineTo(cx - stem_w / 2, stem_top + stem_w / 2)
    path.arcTo(cx - stem_w / 2, stem_top, stem_w, stem_w, 180, -180)
    path.lineTo(cx + stem_w / 2, stem_bottom)

    # Bulb at base
    bulb_r = size * 0.16
    bulb_cy = cy + size * 0.24
    bulb_rect = QRectF(cx - bulb_r, bulb_cy - bulb_r, bulb_r * 2, bulb_r * 2)
    path.arcTo(bulb_rect, 60, -300)
    path.closeSubpath()

    painter.drawPath(path)

    # Filled mercury core
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawEllipse(QPointF(cx, bulb_cy), bulb_r * 0.65, bulb_r * 0.65)
    painter.drawRoundedRect(QRectF(cx - stem_w * 0.22, cy - size * 0.1, stem_w * 0.44, size * 0.25), 1.0, 1.0)

    # 2 Graduation ticks on right side
    painter.setPen(QPen(color, stroke_width * 0.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(cx + stem_w * 0.8, cy - size * 0.15), QPointF(cx + stem_w * 1.5, cy - size * 0.15))
    painter.drawLine(QPointF(cx + stem_w * 0.8, cy - size * 0.0), QPointF(cx + stem_w * 1.5, cy - size * 0.0))
    painter.restore()


def draw_lamp_bulb_icon(painter: QPainter, rect: QRectF, color: QColor, is_on: bool = True, glow_color: QColor = None):
    """Draws Apple HomeKit-style lightbulb vector with dome, neck, threads, and contact."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    cx = rect.center().x()
    cy = rect.center().y()
    size = min(rect.width(), rect.height())
    scale = size / 32.0

    # Bulb dome path
    path = QPainterPath()
    path.moveTo(cx - 5.0 * scale, cy + 3.0 * scale)
    path.cubicTo(
        cx - 10.0 * scale, cy - 2.0 * scale,
        cx - 9.0 * scale, cy - 12.0 * scale,
        cx, cy - 12.0 * scale
    )
    path.cubicTo(
        cx + 9.0 * scale, cy - 12.0 * scale,
        cx + 10.0 * scale, cy - 2.0 * scale,
        cx + 5.0 * scale, cy + 3.0 * scale
    )
    path.lineTo(cx + 4.0 * scale, cy + 6.0 * scale)
    path.lineTo(cx - 4.0 * scale, cy + 6.0 * scale)
    path.closeSubpath()

    bulb_fill = color if is_on else QColor("#475569")
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bulb_fill))
    painter.drawPath(path)

    # Base threads
    painter.setBrush(QBrush(QColor("#64748b")))
    painter.drawRoundedRect(QRectF(cx - 4.0 * scale, cy + 6.5 * scale, 8.0 * scale, 4.0 * scale), 1.2 * scale, 1.2 * scale)

    # Bottom contact
    painter.setBrush(QBrush(QColor("#334155")))
    painter.drawRoundedRect(QRectF(cx - 2.0 * scale, cy + 10.8 * scale, 4.0 * scale, 1.8 * scale), 0.8 * scale, 0.8 * scale)

    # Filament highlight when ON
    if is_on:
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx - 2.5 * scale, cy - 3.0 * scale), QPointF(cx, cy - 5.5 * scale))
        painter.drawLine(QPointF(cx, cy - 5.5 * scale), QPointF(cx + 2.5 * scale, cy - 3.0 * scale))

    painter.restore()


def draw_light_strip_icon(painter: QPainter, rect: QRectF, color: QColor, is_on: bool = True):
    """Draws Apple HomeKit-style LED light strip ribbon with emitting nodes."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    cx = rect.center().x()
    cy = rect.center().y()
    size = min(rect.width(), rect.height())
    scale = size / 32.0

    # Curved Ribbon Strip
    ribbon_path = QPainterPath()
    ribbon_path.moveTo(cx - 12.0 * scale, cy + 6.0 * scale)
    ribbon_path.cubicTo(
        cx - 6.0 * scale, cy + 8.0 * scale,
        cx - 4.0 * scale, cy - 6.0 * scale,
        cx + 2.0 * scale, cy - 4.0 * scale
    )
    ribbon_path.cubicTo(
        cx + 8.0 * scale, cy - 2.0 * scale,
        cx + 10.0 * scale, cy + 4.0 * scale,
        cx + 13.0 * scale, cy + 2.0 * scale
    )

    # Ribbon background track
    painter.setPen(QPen(QColor("#334155"), 4.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(ribbon_path)

    # Glowing surface
    glow_col = color if is_on else QColor("#64748b")
    painter.setPen(QPen(glow_col, 2.2 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(ribbon_path)

    # 4 Surface Mount LED nodes
    node_coords = [
        (cx - 10.0 * scale, cy + 6.3 * scale),
        (cx - 4.0 * scale, cy + 0.5 * scale),
        (cx + 2.0 * scale, cy - 3.8 * scale),
        (cx + 9.5 * scale, cy + 2.8 * scale),
    ]
    painter.setPen(Qt.PenStyle.NoPen)
    node_color = QColor("#ffffff") if is_on else QColor("#94a3b8")
    painter.setBrush(QBrush(node_color))
    for nx, ny in node_coords:
        painter.drawRoundedRect(QRectF(nx - 1.2 * scale, ny - 1.2 * scale, 2.4 * scale, 2.4 * scale), 0.5 * scale, 0.5 * scale)

    painter.restore()


def draw_scene_vector_icon(painter: QPainter, rect: QRectF, scene_type: str, color: QColor):
    """Draws resolution-independent vector icons for lighting scenes."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    cx = rect.center().x()
    cy = rect.center().y()
    size = min(rect.width(), rect.height())
    scale = size / 32.0

    pen = QPen(color, 2.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    st = scene_type.lower()
    if "wave" in st or "aurora" in st or "rainbow" in st:
        # Tri-arc spectrum waves
        for r_factor in [5.0, 8.5, 12.0]:
            r = r_factor * scale
            arc_r = QRectF(cx - r, cy - r * 0.7, r * 2, r * 2)
            painter.drawArc(arc_r, int(30 * 16), int(120 * 16))

    elif "breath" in st or "soft" in st or "pulse" in st:
        # Harmonic smooth sine wave
        wave_path = QPainterPath()
        wave_path.moveTo(cx - 10.0 * scale, cy)
        wave_path.cubicTo(
            cx - 5.0 * scale, cy - 7.0 * scale,
            cx - 5.0 * scale, cy - 7.0 * scale,
            cx, cy
        )
        wave_path.cubicTo(
            cx + 5.0 * scale, cy + 7.0 * scale,
            cx + 5.0 * scale, cy + 7.0 * scale,
            cx + 10.0 * scale, cy
        )
        painter.drawPath(wave_path)
        # Pulsing center dot
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, cy), 2.2 * scale, 2.2 * scale)

    elif "candle" in st or "hearth" in st or "relax" in st:
        # Elegant organic flame teardrop
        flame = QPainterPath()
        flame.moveTo(cx, cy - 10.0 * scale)
        flame.cubicTo(
            cx + 6.0 * scale, cy - 2.0 * scale,
            cx + 6.0 * scale, cy + 7.0 * scale,
            cx, cy + 9.0 * scale
        )
        flame.cubicTo(
            cx - 6.0 * scale, cy + 7.0 * scale,
            cx - 6.0 * scale, cy - 2.0 * scale,
            cx, cy - 10.0 * scale
        )
        painter.setBrush(QBrush(color))
        painter.drawPath(flame)

    elif "read" in st:
        # Minimalist geometric open book pages
        book = QPainterPath()
        # Left page
        book.moveTo(cx, cy + 7.0 * scale)
        book.cubicTo(cx - 4.0 * scale, cy + 5.0 * scale, cx - 8.0 * scale, cy + 6.0 * scale, cx - 10.0 * scale, cy + 7.0 * scale)
        book.lineTo(cx - 10.0 * scale, cy - 6.0 * scale)
        book.cubicTo(cx - 8.0 * scale, cy - 7.0 * scale, cx - 4.0 * scale, cy - 6.0 * scale, cx, cy - 4.0 * scale)
        # Right page
        book.cubicTo(cx + 4.0 * scale, cy - 6.0 * scale, cx + 8.0 * scale, cy - 7.0 * scale, cx + 10.0 * scale, cy - 6.0 * scale)
        book.lineTo(cx + 10.0 * scale, cy + 7.0 * scale)
        book.cubicTo(cx + 8.0 * scale, cy + 6.0 * scale, cx + 4.0 * scale, cy + 5.0 * scale, cx, cy + 7.0 * scale)
        painter.drawPath(book)
        painter.drawLine(QPointF(cx, cy - 4.0 * scale), QPointF(cx, cy + 7.0 * scale))

    elif "focus" in st or "work" in st:
        # Concentric focus reticle
        painter.drawEllipse(QPointF(cx, cy), 9.0 * scale, 9.0 * scale)
        painter.drawEllipse(QPointF(cx, cy), 4.5 * scale, 4.5 * scale)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, cy), 1.8 * scale, 1.8 * scale)

    elif "night" in st or "moon" in st:
        # Minimalist crescent moon
        moon = QPainterPath()
        moon.moveTo(cx + 3.0 * scale, cy - 9.0 * scale)
        moon.cubicTo(
            cx - 7.0 * scale, cy - 7.0 * scale,
            cx - 7.0 * scale, cy + 7.0 * scale,
            cx + 3.0 * scale, cy + 9.0 * scale
        )
        moon.cubicTo(
            cx - 2.0 * scale, cy + 5.0 * scale,
            cx - 2.0 * scale, cy - 5.0 * scale,
            cx + 3.0 * scale, cy - 9.0 * scale
        )
        painter.setBrush(QBrush(color))
        painter.drawPath(moon)

    elif "disco" in st or "party" in st:
        # 8-point geometric energy starburst
        star = QPainterPath()
        for i in range(8):
            ang = i * (math.pi / 4.0)
            ang_half = ang + (math.pi / 8.0)
            r_out = 9.5 * scale
            r_in = 4.0 * scale
            if i == 0:
                star.moveTo(cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out)
            else:
                star.lineTo(cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out)
            star.lineTo(cx + math.cos(ang_half) * r_in, cy + math.sin(ang_half) * r_in)
        star.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.drawPath(star)

    else:
        # Default elegant diamond
        painter.drawPolygon([
            QPointF(cx, cy - 8.0 * scale),
            QPointF(cx + 8.0 * scale, cy),
            QPointF(cx, cy + 8.0 * scale),
            QPointF(cx - 8.0 * scale, cy),
        ])

    painter.restore()


def draw_plus_icon(painter: QPainter, rect: QRectF, color: QColor, stroke_width: float = 2.0):
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    cx, cy = rect.center().x(), rect.center().y()
    d = min(rect.width(), rect.height()) * 0.28
    painter.drawLine(QPointF(cx - d, cy), QPointF(cx + d, cy))
    painter.drawLine(QPointF(cx, cy - d), QPointF(cx, cy + d))
    painter.restore()


def draw_minus_icon(painter: QPainter, rect: QRectF, color: QColor, stroke_width: float = 2.0):
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    cx, cy = rect.center().x(), rect.center().y()
    d = min(rect.width(), rect.height()) * 0.28
    painter.drawLine(QPointF(cx - d, cy), QPointF(cx + d, cy))
    painter.restore()


def draw_sound_icon(painter: QPainter, rect: QRectF, color: QColor, is_muted: bool = False):
    """Draws modern minimalist audio speaker vector with wave or mute slash."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    cx, cy = rect.center().x(), rect.center().y()
    size = min(rect.width(), rect.height())
    scale = size / 32.0

    pen = QPen(color, 1.8 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(QBrush(color))

    # Speaker cone
    cone = QPainterPath()
    cone.moveTo(cx - 6.0 * scale, cy - 3.0 * scale)
    cone.lineTo(cx - 3.0 * scale, cy - 3.0 * scale)
    cone.lineTo(cx + 2.0 * scale, cy - 7.0 * scale)
    cone.lineTo(cx + 2.0 * scale, cy + 7.0 * scale)
    cone.lineTo(cx - 3.0 * scale, cy + 3.0 * scale)
    cone.lineTo(cx - 6.0 * scale, cy + 3.0 * scale)
    cone.closeSubpath()
    painter.drawPath(cone)

    painter.setBrush(Qt.BrushStyle.NoBrush)
    if is_muted:
        # Diagonal slash
        pen_slash = QPen(QColor("#ef4444"), 2.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_slash)
        painter.drawLine(QPointF(cx - 7.0 * scale, cy + 8.0 * scale), QPointF(cx + 8.0 * scale, cy - 8.0 * scale))
    else:
        # Dual sound waves
        arc1 = QRectF(cx + 1.0 * scale, cy - 4.5 * scale, 6.0 * scale, 9.0 * scale)
        painter.drawArc(arc1, int(-45 * 16), int(90 * 16))
        arc2 = QRectF(cx + 3.0 * scale, cy - 8.0 * scale, 9.0 * scale, 16.0 * scale)
        painter.drawArc(arc2, int(-45 * 16), int(90 * 16))

    painter.restore()


def create_vector_pixmap(draw_fn, width: int = 32, height: int = 32, **kwargs) -> QPixmap:
    """Helper to render any vector draw function into a cached transparent QPixmap."""
    pm = QPixmap(width, height)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    rect = QRectF(0, 0, width, height)
    draw_fn(painter, rect, **kwargs)
    painter.end()
    return pm
