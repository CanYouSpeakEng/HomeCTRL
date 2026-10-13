"""
ui.py - Bespoke Commercial Apple HomeKit Control Interface for HomeCTRL.

Features:
- Pure custom vector rendering for all icons (zero generic emojis or stock icons).
- Custom interactive Hue-Saturation Color Wheel with real-time RGB/Hex chips.
- Hardware Dynamic Scenes (Aurora Flow, Ocean Breath, Neon Pulse, Amber Hearth, Disco Jump)
  and curated atmospheric static lighting.
- Fluid entrance and dismissal animations (slide-up + fade-in via QPropertyAnimation).
- Tactile haptic sound design (airy panel pop, resonant switch clicks, tactile ticks).
- Non-blocking execution via QThreadPool (0 lag, thread-safe).
"""

import os
import sys
import time
import winreg
from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt,
    QPoint,
    QPointF,
    QRectF,
    QTimer,
    QObject,
    QRunnable,
    QThreadPool,
    Signal,
    QEvent,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QAction,
    QFont,
    QCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStackedWidget,
    QGraphicsDropShadowEffect,
)

import theme
import icons
from sound import SoundFX
from color_wheel import ColorWheelSection
from lamp import LampDevice, DeviceManager, get_device_manager, SCENE_CATALOG

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "HomeCTRL"


def is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def set_autostart_enabled(enabled: bool) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    python_exe = sys.executable
                    pythonw = python_exe.replace("python.exe", "pythonw.exe")
                    exe = pythonw if os.path.exists(pythonw) else python_exe
                    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
                    cmd = f'"{exe}" "{main_py}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            return True
    except Exception as e:
        print(f"[Autostart Error] {e}")
        return False


# =========================================================================
# Custom Vector Interactive Widgets
# =========================================================================

class VectorPowerButton(QPushButton):
    """Circular Apple Home power button with custom vector power icon."""

    def __init__(self, parent=None, size: int = 48):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_on: bool = False

    def set_on(self, is_on: bool):
        self._is_on = is_on
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        bg_hex = theme.POWER_ON_BG if self._is_on else theme.POWER_OFF_BG
        border_hex = theme.POWER_ON_BORDER if self._is_on else theme.POWER_OFF_BORDER
        bg_color = QColor(bg_hex)
        border_color = QColor(border_hex)

        if self.isDown():
            bg_color = bg_color.darker(115)
        elif self.underMouse():
            bg_color = bg_color.lighter(110)

        # Background circle
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.5))
        painter.drawEllipse(rect.adjusted(1, 1, -1, -1))

        # Vector Power symbol
        icon_color = QColor(theme.POWER_ON_FG if self._is_on else theme.TEXT_MUTED)
        icons.draw_power_icon(painter, rect, icon_color, stroke_width=2.5)
        painter.end()


class StepButton(QPushButton):
    """Custom minimalist vector step button (+ / -) for sliders."""

    def __init__(self, is_plus: bool, parent=None, size: int = 28):
        super().__init__(parent)
        self.is_plus = is_plus
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        bg_color = QColor(theme.BG_CARD_HOVER if self.underMouse() else theme.BG_CARD)
        if self.isDown():
            bg_color = bg_color.darker(120)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(theme.BORDER_GLASS), 1.0))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        pen_color = QColor(theme.TEXT_PRIMARY)
        if self.is_plus:
            icons.draw_plus_icon(painter, rect, pen_color, stroke_width=1.8)
        else:
            icons.draw_minus_icon(painter, rect, pen_color, stroke_width=1.8)
        painter.end()


class AudioToggleButton(QPushButton):
    """Clean header button to toggle tactile audio feedback."""

    def __init__(self, parent=None, size: int = 28):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Toggle Tactile Sound Effects")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        bg_color = QColor(theme.BG_CARD_HOVER if self.underMouse() else theme.BG_CARD)
        if self.isDown():
            bg_color = bg_color.darker(120)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(theme.BORDER_GLASS), 1.0))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        is_muted = not SoundFX.is_enabled()
        pen_color = QColor(theme.TEXT_SECONDARY if not is_muted else theme.TEXT_MUTED)
        icons.draw_sound_icon(painter, rect, pen_color, is_muted=is_muted)
        painter.end()


class HeroDeviceIconWidget(QWidget):
    """Live vector hero light icon with glowing aura."""

    def __init__(self, parent=None, size: int = 42):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._is_on: bool = False
        self._rgb: tuple = (255, 255, 255)
        self._is_strip: bool = False

    def update_state(self, is_on: bool, rgb: tuple, is_strip: bool = False):
        self._is_on = is_on
        self._rgb = rgb
        self._is_strip = is_strip
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        glow_col = QColor(self._rgb[0], self._rgb[1], self._rgb[2]) if self._is_on else QColor(theme.TEXT_MUTED)

        if self._is_strip:
            icons.draw_light_strip_icon(painter, rect, glow_col, is_on=self._is_on)
        else:
            icons.draw_lamp_bulb_icon(painter, rect, glow_col, is_on=self._is_on)
        painter.end()


class SceneCardWidget(QFrame):
    """Custom squircle scene card with custom vector icon and active state."""

    clicked = Signal(str)  # Emits scene_id

    def __init__(self, scene_id: str, label: str, icon_key: str, desc: str, color_hint: str, is_dynamic: bool, parent=None):
        super().__init__(parent)
        self.scene_id = scene_id
        self.label = label
        self.icon_key = icon_key
        self.desc = desc
        self.color_hint = color_hint
        self.is_dynamic = is_dynamic
        self._is_active = False

        self.setFixedHeight(58)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Vector Icon Box
        self.icon_box = QWidget(self)
        self.icon_box.setFixedSize(30, 30)
        self.icon_box.paintEvent = self._paint_icon
        layout.addWidget(self.icon_box)

        # Label & Desc Column
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_row = QHBoxLayout()
        lbl_row.setSpacing(6)

        title_lbl = QLabel(self.label, self)
        title_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-family: '{theme.FONT_FAMILY}'; font-size: 9.5pt; font-weight: 600;")
        lbl_row.addWidget(title_lbl)

        if self.is_dynamic:
            badge = QLabel("FLOW", self)
            badge.setStyleSheet(
                "background-color: rgba(14, 165, 233, 0.2); color: #38bdf8; "
                "font-size: 7pt; font-weight: 700; border-radius: 4px; padding: 1px 4px;"
            )
            lbl_row.addWidget(badge)

        lbl_row.addStretch()
        text_col.addLayout(lbl_row)

        desc_lbl = QLabel(self.desc, self)
        desc_lbl.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-family: '{theme.FONT_FAMILY}'; font-size: 7.5pt;")
        text_col.addWidget(desc_lbl)

        layout.addLayout(text_col)
        layout.addStretch()

    def _paint_icon(self, event):
        painter = QPainter(self.icon_box)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.icon_box.rect())
        col = QColor(self.color_hint)
        icons.draw_scene_vector_icon(painter, rect, self.icon_key, col)
        painter.end()

    def set_active(self, active: bool):
        self._is_active = active
        self._update_style()

    def _update_style(self):
        border = f"1.5px solid {self.color_hint}" if self._is_active else f"1px solid {theme.BORDER_GLASS}"
        bg = "rgba(36, 40, 50, 0.9)" if self._is_active else theme.BG_CARD
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
                border: {border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {theme.BG_CARD_HOVER};
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            """
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            SoundFX.play_tick()
            self.clicked.emit(self.scene_id)


# =========================================================================
# Background Worker Task
# =========================================================================

class WorkerSignals(QObject):
    finished = Signal(dict)
    error = Signal(str)


class LampTask(QRunnable):
    """Executes hardware Tuya actions off the main GUI thread."""

    def __init__(self, action: str, lamp: LampDevice, **kwargs):
        super().__init__()
        self.action = action
        self.lamp = lamp
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            if self.action == "toggle":
                self.lamp.toggle()
            elif self.action == "turn_on":
                self.lamp.turn_on()
            elif self.action == "turn_off":
                self.lamp.turn_off()
            elif self.action == "brightness":
                val = self.kwargs.get("val", 50)
                self.lamp.set_brightness(val)
            elif self.action == "color_temp":
                val = self.kwargs.get("val", 50)
                self.lamp.set_color_temp(val)
            elif self.action == "rgb":
                r = self.kwargs.get("r", 255)
                g = self.kwargs.get("g", 255)
                b = self.kwargs.get("b", 255)
                self.lamp.set_rgb(r, g, b)
            elif self.action == "scene":
                scene_id = self.kwargs.get("scene_id", "")
                self.lamp.apply_named_scene(scene_id)
            elif self.action == "refresh":
                self.lamp.refresh_status()

            state = self.lamp.get_state_dict()
            self.signals.finished.emit(state)
        except Exception as e:
            self.signals.error.emit(str(e))


# =========================================================================
# Floating Apple HomeKit Control Card
# =========================================================================

class PopupPanel(QWidget):
    """The main Apple HomeKit floating control card with entrance animations."""

    def __init__(self, manager: DeviceManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.active_tasks = set()
        self.last_hide_timestamp = 0.0
        self._target_pos = QPoint(0, 0)
        self._is_closing = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(theme.PANEL_WIDTH, theme.PANEL_HEIGHT)

        self._setup_animations()
        self._init_ui()

    @property
    def lamp(self) -> LampDevice:
        return self.manager.current

    def _setup_animations(self):
        """Prepares smooth spring entrance and dismissal animations."""
        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(220)
        self.anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_pos = QPropertyAnimation(self, b"pos")
        self.anim_pos.setDuration(220)
        self.anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group = QParallelAnimationGroup(self)
        self.anim_group.addAnimation(self.anim_opacity)
        self.anim_group.addAnimation(self.anim_pos)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)

        # Frosted Glass Card Container
        self.card = QFrame(self)
        self.card.setObjectName("ContainerFrame")
        self.card.setStyleSheet(theme.get_panel_stylesheet())

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(theme.SHADOW_BLUR_RADIUS)
        shadow.setColor(theme.SHADOW_COLOR)
        shadow.setOffset(theme.SHADOW_OFFSET_X, theme.SHADOW_OFFSET_Y)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(14)

        # 1. Top Header Bar (App Branding + Sound Toggle + Master Blackout)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        app_title = QLabel("HomeCTRL", self.card)
        app_title.setFont(theme.FONT_HERO)
        app_title.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")

        self.audio_btn = AudioToggleButton(self.card, size=28)
        self.audio_btn.clicked.connect(self._on_toggle_audio)

        self.all_off_btn = QPushButton("All Off", self.card)
        self.all_off_btn.setFixedHeight(28)
        self.all_off_btn.setProperty("class", "action-pill")
        self.all_off_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.all_off_btn.clicked.connect(self._on_all_off_clicked)

        top_bar.addWidget(app_title)
        top_bar.addStretch()
        top_bar.addWidget(self.audio_btn)
        top_bar.addWidget(self.all_off_btn)
        card_layout.addLayout(top_bar)

        # 2. Multi-Device Segmented Bar
        device_bar = QFrame(self.card)
        device_bar.setObjectName("SegmentBar")
        dev_bar_layout = QHBoxLayout(device_bar)
        dev_bar_layout.setContentsMargins(4, 4, 4, 4)
        dev_bar_layout.setSpacing(4)

        self.device_tab_btns = []
        for idx, dev in enumerate(self.manager.devices):
            btn = QPushButton(dev.name, device_bar)
            btn.setProperty("class", "segment-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "true" if idx == self.manager.active_index else "false")
            btn.clicked.connect(lambda _, i=idx: self._on_switch_device(i))
            dev_bar_layout.addWidget(btn)
            self.device_tab_btns.append(btn)

        card_layout.addWidget(device_bar)

        # 3. Hero Device Squircle Tile
        hero_card = QFrame(self.card)
        hero_card.setObjectName("DeviceCard")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(14, 14, 14, 14)
        hero_layout.setSpacing(12)

        # Custom Vector Glow Icon
        self.hero_icon = HeroDeviceIconWidget(hero_card, size=40)
        hero_layout.addWidget(self.hero_icon)

        # Device Info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        self.hero_title = QLabel(self.lamp.name, hero_card)
        self.hero_title.setFont(theme.FONT_TITLE)

        self.hero_status = QLabel("Checking...", hero_card)
        self.hero_status.setFont(theme.FONT_SMALL)
        self.hero_status.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")

        info_col.addWidget(self.hero_title)
        info_col.addWidget(self.hero_status)
        hero_layout.addLayout(info_col)

        hero_layout.addStretch()

        # Vector Power Toggle Button
        self.power_btn = VectorPowerButton(hero_card, size=48)
        self.power_btn.clicked.connect(self._on_power_clicked)
        hero_layout.addWidget(self.power_btn)

        card_layout.addWidget(hero_card)

        # 4. Mode Segmented Navigation (White | Colors | Scenes)
        mode_bar = QFrame(self.card)
        mode_bar.setObjectName("SegmentBar")
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(4, 4, 4, 4)
        mode_layout.setSpacing(4)

        self.mode_btns = []
        for idx, (m_id, m_label) in enumerate([("white", "White"), ("color", "Colors"), ("scenes", "Scenes")]):
            btn = QPushButton(m_label, mode_bar)
            btn.setProperty("class", "segment-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda _, i=idx: self._on_switch_mode(i))
            mode_layout.addWidget(btn)
            self.mode_btns.append(btn)

        card_layout.addWidget(mode_bar)

        # 5. Stacked Pages
        self.stack = QStackedWidget(self.card)

        # Page 1: White Mode (Sliders)
        self.white_page = self._build_white_page()
        self.stack.addWidget(self.white_page)

        # Page 2: Colors Mode (Bespoke Interactive Color Wheel)
        self.colors_page = self._build_colors_page()
        self.stack.addWidget(self.colors_page)

        # Page 3: Scenes Mode (Hardware Dynamic + Static Cards)
        self.scenes_page = self._build_scenes_page()
        self.stack.addWidget(self.scenes_page)

        card_layout.addWidget(self.stack)

        # 6. Footer Connection Bar
        card_layout.addStretch()
        footer_row = QHBoxLayout()
        footer_row.setSpacing(6)

        self.footer_dot = QLabel(self.card)
        self.footer_dot.setFixedSize(8, 8)
        self._set_status_dot_color(theme.STATUS_ONLINE)

        self.footer_label = QLabel(self.card)
        self.footer_label.setFont(theme.FONT_SMALL)
        self.footer_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")

        footer_row.addWidget(self.footer_dot)
        footer_row.addWidget(self.footer_label)
        footer_row.addStretch()

        card_layout.addLayout(footer_row)
        root_layout.addWidget(self.card)

    def _build_white_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)

        # Brightness Section
        b_header = QHBoxLayout()
        b_title = QLabel("Brightness", page)
        b_title.setFont(theme.FONT_BOLD)
        self.bright_val_label = QLabel("50%", page)
        self.bright_val_label.setFont(theme.FONT_BOLD)
        self.bright_val_label.setStyleSheet(f"color: {theme.ACCENT_AMBER};")
        b_header.addWidget(b_title)
        b_header.addStretch()
        b_header.addWidget(self.bright_val_label)
        layout.addLayout(b_header)

        b_row = QHBoxLayout()
        b_row.setSpacing(8)
        self.minus_btn = StepButton(is_plus=False, parent=page, size=30)
        self.minus_btn.clicked.connect(self._on_minus_clicked)

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal, page)
        self.brightness_slider.setObjectName("BrightnessSlider")
        self.brightness_slider.setRange(10, 100)
        self.brightness_slider.setValue(self.lamp.brightness)
        self.brightness_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.brightness_slider.valueChanged.connect(self._on_slider_value_changed)
        self.brightness_slider.sliderReleased.connect(self._commit_slider_brightness)

        self.plus_btn = StepButton(is_plus=True, parent=page, size=30)
        self.plus_btn.clicked.connect(self._on_plus_clicked)

        b_row.addWidget(self.minus_btn)
        b_row.addWidget(self.brightness_slider)
        b_row.addWidget(self.plus_btn)
        layout.addLayout(b_row)

        # Color Temperature Section
        t_header = QHBoxLayout()
        t_title = QLabel("Color Temperature", page)
        t_title.setFont(theme.FONT_BOLD)
        self.temp_val_label = QLabel("Neutral (4000K)", page)
        self.temp_val_label.setFont(theme.FONT_SMALL)
        self.temp_val_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        t_header.addWidget(t_title)
        t_header.addStretch()
        t_header.addWidget(self.temp_val_label)
        layout.addLayout(t_header)

        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        self.warm_btn = StepButton(is_plus=False, parent=page, size=30)
        self.warm_btn.clicked.connect(lambda: self._step_color_temp(-15))

        self.temp_slider = QSlider(Qt.Orientation.Horizontal, page)
        self.temp_slider.setObjectName("TempSlider")
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(self.lamp.color_temp)
        self.temp_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.temp_slider.valueChanged.connect(self._on_temp_value_changed)
        self.temp_slider.sliderReleased.connect(self._commit_temp_slider)

        self.cool_btn = StepButton(is_plus=True, parent=page, size=30)
        self.cool_btn.clicked.connect(lambda: self._step_color_temp(15))

        t_row.addWidget(self.warm_btn)
        t_row.addWidget(self.temp_slider)
        t_row.addWidget(self.cool_btn)
        layout.addLayout(t_row)

        return page

    def _build_colors_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(10)

        # Bespoke Custom Color Wheel
        self.color_section = ColorWheelSection(page)
        self.color_section.colorSelected.connect(self._on_custom_color_selected)
        layout.addWidget(self.color_section)

        return page

    def _build_scenes_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        self.scene_cards = []
        for idx, sc in enumerate(theme.SCENES):
            row = idx // 2
            col = idx % 2
            card = SceneCardWidget(
                scene_id=sc["id"],
                label=sc["label"],
                icon_key=sc["icon_key"],
                desc=sc["desc"],
                color_hint=sc["color_hint"],
                is_dynamic=(sc.get("type") == "dynamic"),
                parent=page
            )
            card.clicked.connect(self._on_scene_clicked)
            layout.addWidget(card, row, col)
            self.scene_cards.append(card)

        return page

    # =========================================================================
    # User Interactions & Handlers
    # =========================================================================

    def _on_toggle_audio(self):
        new_state = not SoundFX.is_enabled()
        SoundFX.set_enabled(new_state)
        self.audio_btn.update()
        if new_state:
            SoundFX.play_tick()

    def _on_switch_device(self, index: int):
        if index == self.manager.active_index:
            return
        SoundFX.play_tick()
        self.manager.set_active(index)
        for i, btn in enumerate(self.device_tab_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._update_ui_state(self.lamp.get_state_dict())
        self._run_worker("refresh")

    def _on_all_off_clicked(self):
        SoundFX.play_switch_off()
        self.manager.turn_all_off()
        self._update_ui_state(self.lamp.get_state_dict())

    def _on_power_clicked(self):
        if self.lamp.is_on:
            SoundFX.play_switch_off()
        else:
            SoundFX.play_switch_on()
        self._run_worker("toggle")

    def _on_switch_mode(self, index: int):
        SoundFX.play_tick()
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.mode_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_slider_value_changed(self, value: int):
        self.bright_val_label.setText(f"{value}%")

    def _commit_slider_brightness(self):
        SoundFX.play_tick()
        val = self.brightness_slider.value()
        self._run_worker("brightness", val=val)

    def _on_minus_clicked(self):
        val = max(10, self.brightness_slider.value() - 10)
        self.brightness_slider.setValue(val)
        self._commit_slider_brightness()

    def _on_plus_clicked(self):
        val = min(100, self.brightness_slider.value() + 10)
        self.brightness_slider.setValue(val)
        self._commit_slider_brightness()

    def _on_temp_value_changed(self, value: int):
        kelvin = int(2700 + (value / 100.0) * (6500 - 2700))
        label_text = f"Warm ({kelvin}K)" if value < 35 else (f"Cool ({kelvin}K)" if value > 65 else f"Neutral ({kelvin}K)")
        self.temp_val_label.setText(label_text)

    def _commit_temp_slider(self):
        SoundFX.play_tick()
        val = self.temp_slider.value()
        self._run_worker("color_temp", val=val)

    def _step_color_temp(self, delta: int):
        val = max(0, min(100, self.temp_slider.value() + delta))
        self.temp_slider.setValue(val)
        self._commit_temp_slider()

    def _on_custom_color_selected(self, rgb: tuple):
        r, g, b = rgb
        self.hero_icon.update_state(is_on=True, rgb=rgb, is_strip=("Strip" in self.lamp.name))
        self._run_worker("rgb", r=r, g=g, b=b)

    def _on_scene_clicked(self, scene_id: str):
        for card in self.scene_cards:
            card.set_active(card.scene_id == scene_id)
        self._run_worker("scene", scene_id=scene_id)

    # =========================================================================
    # Thread-Safe Hardware Communication
    # =========================================================================

    def _run_worker(self, action: str, **kwargs):
        task = LampTask(action, self.lamp, **kwargs)
        task.signals.finished.connect(self._on_task_finished)
        task.signals.error.connect(self._on_task_error)
        self.active_tasks.add(task)
        QThreadPool.globalInstance().start(task)

    def _on_task_finished(self, state: dict):
        # Clean finished task
        sender_task = self.sender()
        self.active_tasks = {t for t in self.active_tasks if t != sender_task}
        self._update_ui_state(state)

    def _on_task_error(self, err: str):
        sender_task = self.sender()
        self.active_tasks = {t for t in self.active_tasks if t != sender_task}
        self.footer_label.setText(f"Error: {err}")
        self._set_status_dot_color(theme.STATUS_OFFLINE)

    def _update_ui_state(self, state: dict):
        self.hero_title.setText(state.get("name", self.lamp.name))

        is_on = state.get("is_on", False)
        is_online = state.get("is_online", False)
        bright = state.get("brightness", 50)
        temp = state.get("color_temp", 50)
        work_mode = state.get("work_mode", "white")
        rgb = state.get("rgb", (255, 255, 255))
        channel = state.get("active_channel", "cloud").capitalize()
        is_strip = "Strip" in state.get("name", "")

        # Update Hero Tile
        self.hero_icon.update_state(is_on=is_on, rgb=rgb, is_strip=is_strip)
        self.power_btn.set_on(is_on)

        if not self.brightness_slider.isSliderDown():
            self.brightness_slider.setValue(bright)
            self.bright_val_label.setText(f"{bright}%")

        if not self.temp_slider.isSliderDown():
            self.temp_slider.setValue(temp)
            self._on_temp_value_changed(temp)

        if work_mode == "colour":
            self.color_section.set_current_rgb(rgb[0], rgb[1], rgb[2])

        # Status labels
        if not is_online:
            self.hero_status.setText("Offline • Check Connection")
            self.hero_status.setStyleSheet(f"color: {theme.STATUS_OFFLINE};")
            self._set_status_dot_color(theme.STATUS_OFFLINE)
            self.footer_label.setText(f"Offline • {channel}")
        elif not is_on:
            self.hero_status.setText("Powered Off")
            self.hero_status.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
            self._set_status_dot_color(theme.STATUS_ONLINE)
            self.footer_label.setText(f"Standby • {channel}")
        else:
            mode_desc = "White" if work_mode == "white" else ("Color" if work_mode == "colour" else "Dynamic Scene")
            self.hero_status.setText(f"On • {bright}% • {mode_desc}")
            self.hero_status.setStyleSheet(f"color: {theme.STATUS_ONLINE};")
            self._set_status_dot_color(theme.STATUS_ONLINE)
            self.footer_label.setText(f"Connected • {channel}")

    def _set_status_dot_color(self, hex_color: str):
        self.footer_dot.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")

    # =========================================================================
    # Fluid Animations & Dismissal Guards
    # =========================================================================

    def show_animated(self):
        """Calculates bottom-right anchor and executes fluid slide-up entrance."""
        self._is_closing = False
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = geo.right() - self.width() - theme.PANEL_MARGIN_RIGHT
        final_y = geo.bottom() - self.height() - theme.PANEL_MARGIN_BOTTOM
        self._target_pos = QPoint(x, final_y)

        # Start 22px below with 0.0 opacity
        start_pos = QPoint(x, final_y + 22)
        self.move(start_pos)
        self.setWindowOpacity(0.0)

        super().show()
        self.raise_()
        self.activateWindow()

        SoundFX.play_open()

        # Run parallel animation
        self.anim_opacity.stop()
        self.anim_pos.stop()

        self.anim_opacity.setStartValue(0.0)
        self.anim_opacity.setEndValue(1.0)

        self.anim_pos.setStartValue(start_pos)
        self.anim_pos.setEndValue(self._target_pos)

        self.anim_group.start()

        if self.lamp.is_configured:
            self._run_worker("refresh")

    def hide_animated(self):
        """Executes smooth dismissal animation before hiding."""
        if self._is_closing or not self.isVisible():
            return
        self._is_closing = True
        SoundFX.play_close()

        self.anim_opacity.stop()
        self.anim_pos.stop()

        self.anim_opacity.setDuration(160)
        self.anim_opacity.setStartValue(self.windowOpacity())
        self.anim_opacity.setEndValue(0.0)

        current_pos = self.pos()
        target_close_pos = QPoint(current_pos.x(), current_pos.y() + 16)
        self.anim_pos.setDuration(160)
        self.anim_pos.setStartValue(current_pos)
        self.anim_pos.setEndValue(target_close_pos)

        def _on_anim_finished():
            if self._is_closing:
                super(PopupPanel, self).hide()
                self._is_closing = False

        # Disconnect any old finished connections
        try:
            self.anim_group.finished.disconnect()
        except Exception:
            pass
        self.anim_group.finished.connect(_on_anim_finished)
        self.anim_group.start()

    def changeEvent(self, event):
        """Guards against outside-click dismissals while dragging sliders."""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow() and not self._is_closing:
                if hasattr(self, "brightness_slider") and self.brightness_slider.isSliderDown():
                    return
                if hasattr(self, "temp_slider") and self.temp_slider.isSliderDown():
                    return
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                if self.rect().contains(cursor_pos):
                    return
                self.hide_animated()
        super().changeEvent(event)

    def hideEvent(self, event):
        self.last_hide_timestamp = time.time()
        super().hideEvent(event)


# =========================================================================
# System Tray Application
# =========================================================================

def create_tray_pixmap(size: int = 32) -> QPixmap:
    """Renders high-res vector lightbulb tray icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    rect = QRectF(0, 0, size, size)
    icons.draw_lamp_bulb_icon(painter, rect, color=QColor(theme.ACCENT_AMBER), is_on=True)
    painter.end()
    return pm


class TrayApp(QSystemTrayIcon):
    """System tray integration with bespoke context menu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = get_device_manager()
        self.popup = PopupPanel(self.manager)

        self.setIcon(QIcon(create_tray_pixmap(size=32)))
        self.setToolTip("HomeCTRL - Smart Lighting")

        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self):
        menu = QMenu()
        menu.setStyleSheet(
            f"""
            QMenu {{
                background-color: {theme.BG_PANEL};
                color: {theme.TEXT_PRIMARY};
                border: 1px solid {theme.BORDER_GLASS};
                border-radius: 8px;
                padding: 4px;
                font-family: "{theme.FONT_FAMILY}";
                font-size: 10pt;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.BG_CARD_HOVER};
                color: {theme.TEXT_PRIMARY};
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme.BORDER_GLASS};
                margin: 4px 8px;
            }}
            """
        )

        show_action = QAction("Show HomeCTRL", self)
        show_action.triggered.connect(self._on_show_clicked)
        menu.addAction(show_action)

        self.sound_action = QAction("Tactile Sound Effects", self)
        self.sound_action.setCheckable(True)
        self.sound_action.setChecked(SoundFX.is_enabled())
        self.sound_action.triggered.connect(self._on_sound_toggled)
        menu.addAction(self.sound_action)

        self.autostart_action = QAction("Start with Windows", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_autostart_enabled())
        self.autostart_action.triggered.connect(self._on_autostart_toggled)
        menu.addAction(self.autostart_action)

        menu.addSeparator()

        quit_action = QAction("Quit HomeCTRL", self)
        quit_action.triggered.connect(self._on_quit_clicked)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            now = time.time()
            if now - self.popup.last_hide_timestamp < 0.25:
                return
            if self.popup.isVisible():
                self.popup.hide_animated()
            else:
                self.popup.show_animated()

    def _on_show_clicked(self):
        self.popup.show_animated()

    def _on_sound_toggled(self, checked: bool):
        SoundFX.set_enabled(checked)
        self.popup.audio_btn.update()

    def _on_autostart_toggled(self, checked: bool):
        success = set_autostart_enabled(checked)
        self.autostart_action.setChecked(is_autostart_enabled() if not success else checked)

    def _on_quit_clicked(self):
        self.hide()
        QApplication.quit()
