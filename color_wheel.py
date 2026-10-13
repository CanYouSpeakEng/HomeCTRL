"""
color_wheel.py - Bespoke Apple HomeKit Interactive Color Wheel for HomeCTRL.

Renders a continuous conical Hue-Saturation disc with an interactive draggable
selector handle, real-time RGB/Hex preview pill, and quick swatch chips.
Zero generic QColorDialog dependencies. 100% custom QPainter implementation.
"""

import math
import colorsys
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter,
    QPainterPath,
    QColor,
    QPen,
    QBrush,
    QConicalGradient,
    QRadialGradient,
    QPixmap,
    QFont,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
import theme
from sound import SoundFX


class CustomColorWheel(QWidget):
    """
    Continuous circular HSV color disc.
    - Outer edge: 100% saturation of all 360 hues.
    - Center: 0% saturation (pure white / neutral core).
    - Draggable handle smoothly positions on mouse press & drag.
    """

    colorChanged = Signal(QColor)      # Emitted during interactive drag
    colorCommitted = Signal(QColor)    # Emitted on mouse release

    def __init__(self, parent=None, wheel_size: int = 180):
        super().__init__(parent)
        self.wheel_size = wheel_size
        self.setFixedSize(wheel_size, wheel_size)
        self.setMouseTracking(True)

        self._hue: float = 0.0          # 0.0 to 1.0
        self._saturation: float = 1.0   # 0.0 to 1.0
        self._value: float = 1.0        # 0.0 to 1.0
        self._is_dragging: bool = False
        self._wheel_pixmap: QPixmap = None

        self._render_wheel_cache()

    def _render_wheel_cache(self):
        """Pre-renders the conical + radial gradient disc onto a cached QPixmap for 60fps rendering."""
        size = self.wheel_size
        self._wheel_pixmap = QPixmap(size, size)
        self._wheel_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(self._wheel_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        cx, cy = size / 2.0, size / 2.0
        radius = (size / 2.0) - 10.0

        # 1. Base Conical Gradient for 360-degree Hue
        conical = QConicalGradient(cx, cy, 0)
        # 12 rainbow stops around 360 deg
        for step in range(13):
            fraction = step / 12.0
            r, g, b = colorsys.hsv_to_rgb(fraction, 1.0, 1.0)
            conical.setColorAt(fraction, QColor(int(r * 255), int(g * 255), int(b * 255)))

        painter.setBrush(QBrush(conical))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 2. Radial Gradient: Pure White at center -> Transparent at outer edge (creates saturation falloff)
        radial = QRadialGradient(cx, cy, radius)
        radial.setColorAt(0.0, QColor(255, 255, 255, 255))
        radial.setColorAt(0.65, QColor(255, 255, 255, 120))
        radial.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setBrush(QBrush(radial))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 3. Subtle dark glass outer border
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.5))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Draw pre-rendered wheel
        if self._wheel_pixmap:
            painter.drawPixmap(0, 0, self._wheel_pixmap)

        # Calculate current handle coordinates from hue & saturation
        size = self.wheel_size
        cx, cy = size / 2.0, size / 2.0
        max_r = (size / 2.0) - 10.0

        r = self._saturation * max_r
        angle = self._hue * 2.0 * math.pi
        hx = cx + r * math.cos(angle)
        hy = cy + r * math.sin(angle)

        # Draw interactive lens handle
        current_color = self.get_color()

        # Handle outer shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawEllipse(QPointF(hx, hy + 1.5), 11.0, 11.0)

        # Handle white ring
        painter.setPen(QPen(QColor("#ffffff"), 2.5))
        painter.setBrush(QBrush(current_color))
        painter.drawEllipse(QPointF(hx, hy), 9.0, 9.0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._update_color_from_pos(event.position().x(), event.position().y())
            SoundFX.play_tick()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self._update_color_from_pos(event.position().x(), event.position().y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.colorCommitted.emit(self.get_color())
            SoundFX.play_tick()

    def _update_color_from_pos(self, x: float, y: float):
        size = self.wheel_size
        cx, cy = size / 2.0, size / 2.0
        max_r = (size / 2.0) - 10.0

        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy)
        sat = max(0.0, min(1.0, dist / max_r))

        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2.0 * math.pi
        hue = angle / (2.0 * math.pi)

        self._hue = hue
        self._saturation = sat
        self.update()
        self.colorChanged.emit(self.get_color())

    def get_color(self) -> QColor:
        r, g, b = colorsys.hsv_to_rgb(self._hue, self._saturation, self._value)
        return QColor(int(r * 255), int(g * 255), int(b * 255))

    def set_color(self, color: QColor):
        r, g, b = color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        self._hue = h
        self._saturation = s
        self._value = max(0.2, v)
        self.update()


class ColorWheelSection(QWidget):
    """
    Complete HomeKit color selection card:
    - Custom interactive wheel
    - Dynamic Hex and RGB live readout pill
    - Curated 8 quick-touch swatches
    """

    colorSelected = Signal(tuple)  # (r, g, b)

    CURATED_SWATCHES = [
        ("#ff3b30", "Sunset Red"),
        ("#ff9500", "Warm Amber"),
        ("#ffd60a", "Solar Gold"),
        ("#34c759", "Emerald Light"),
        ("#00c7be", "Aqua Marine"),
        ("#0a84ff", "Electric Blue"),
        ("#5e5ce6", "Indigo Deep"),
        ("#bf5af2", "Cyberpunk Pink"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Color Wheel
        self.wheel = CustomColorWheel(self, wheel_size=170)
        self.wheel.colorChanged.connect(self._on_wheel_changed)
        self.wheel.colorCommitted.connect(self._on_wheel_committed)
        layout.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Live Info Pill (Hex + RGB)
        self.info_pill = QFrame()
        self.info_pill.setStyleSheet(
            f"""
            QFrame {{
                background-color: {theme.BG_CARD};
                border: 1px solid {theme.BORDER_GLASS};
                border-radius: 12px;
                padding: 4px 12px;
            }}
            """
        )
        pill_layout = QHBoxLayout(self.info_pill)
        pill_layout.setContentsMargins(8, 4, 8, 4)
        pill_layout.setSpacing(8)

        self.color_dot = QFrame()
        self.color_dot.setFixedSize(14, 14)
        self.color_dot.setStyleSheet("border-radius: 7px; background-color: #ff9500;")
        pill_layout.addWidget(self.color_dot)

        self.hex_label = QLabel("#FF9500")
        self.hex_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-family: '{theme.FONT_FAMILY}'; font-size: 10pt; font-weight: 600;"
        )
        pill_layout.addWidget(self.hex_label)

        self.rgb_label = QLabel("RGB 255, 149, 0")
        self.rgb_label.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; font-family: '{theme.FONT_FAMILY}'; font-size: 8.5pt;"
        )
        pill_layout.addWidget(self.rgb_label)

        layout.addWidget(self.info_pill, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Quick Swatches Row
        swatch_frame = QWidget()
        swatch_layout = QHBoxLayout(swatch_frame)
        swatch_layout.setContentsMargins(0, 2, 0, 2)
        swatch_layout.setSpacing(8)
        swatch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for hex_col, name in self.CURATED_SWATCHES:
            btn = QFrame()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {hex_col};
                    border-radius: 11px;
                    border: 1.5px solid rgba(255, 255, 255, 0.4);
                }}
                QFrame:hover {{
                    border: 2px solid #ffffff;
                }}
                """
            )
            btn.mousePressEvent = lambda e, c=hex_col: self._on_swatch_clicked(c)
            swatch_layout.addWidget(btn)

        layout.addWidget(swatch_frame)

    def _on_wheel_changed(self, color: QColor):
        hex_str = color.name().upper()
        self.hex_label.setText(hex_str)
        self.rgb_label.setText(f"RGB {color.red()}, {color.green()}, {color.blue()}")
        self.color_dot.setStyleSheet(f"border-radius: 7px; background-color: {hex_str};")

    def _on_wheel_committed(self, color: QColor):
        self._on_wheel_changed(color)
        self.colorSelected.emit((color.red(), color.green(), color.blue()))

    def _on_swatch_clicked(self, hex_code: str):
        col = QColor(hex_code)
        self.wheel.set_color(col)
        self._on_wheel_changed(col)
        SoundFX.play_tick()
        self.colorSelected.emit((col.red(), col.green(), col.blue()))

    def set_current_rgb(self, r: int, g: int, b: int):
        col = QColor(r, g, b)
        self.wheel.set_color(col)
        self._on_wheel_changed(col)
