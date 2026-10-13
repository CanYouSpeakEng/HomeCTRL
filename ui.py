"""
ui.py - Commercial Apple HomeKit User Interface for HomeCTRL.

Features:
- Apple HomeKit frosted dark glass design with squircle cards and subtle glow.
- Multi-device control (Light 1 & Desk Strip) with live state indicators.
- Mode Switcher: White Mode (Temp + Brightness), Color Mode (16M Colors), and Scenes.
- Non-blocking execution via QThreadPool (0 lag, no thread destruction crashes).
- Custom vector-drawn icons and system tray integration.
"""

import os
import sys
import time
import winreg
from typing import Optional, List

from PySide6.QtCore import (
    Qt,
    QPoint,
    QPointF,
    QTimer,
    QObject,
    QRunnable,
    QThreadPool,
    Signal,
    QEvent,
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
    QColorDialog,
    QGraphicsDropShadowEffect,
)

import theme
from lamp import LampDevice, DeviceManager, get_device_manager

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


def create_lamp_pixmap(size: int = 32, is_on: bool = True, rgb: tuple = (245, 158, 11)) -> QPixmap:
    """Renders a custom vector-style smart lamp icon dynamically onto a QPixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    scale = size / 32.0

    bulb_color = QColor(rgb[0], rgb[1], rgb[2]) if is_on else QColor(theme.TEXT_MUTED)
    base_color = QColor("#64748b")
    contact_color = QColor("#475569")

    # Bulb dome
    path = QPainterPath()
    path.moveTo(11 * scale, 18 * scale)
    path.cubicTo(6 * scale, 14 * scale, 7 * scale, 4 * scale, 16 * scale, 4 * scale)
    path.cubicTo(25 * scale, 4 * scale, 26 * scale, 14 * scale, 21 * scale, 18 * scale)
    path.lineTo(20 * scale, 21 * scale)
    path.lineTo(12 * scale, 21 * scale)
    path.closeSubpath()

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bulb_color))
    painter.drawPath(path)

    # Base threads
    painter.setBrush(QBrush(base_color))
    painter.drawRoundedRect(12 * scale, 21.5 * scale, 8 * scale, 4.5 * scale, 1.5 * scale, 1.5 * scale)

    # Base contact
    painter.setBrush(QBrush(contact_color))
    painter.drawRoundedRect(14 * scale, 26 * scale, 4 * scale, 2 * scale, 1.0 * scale, 1.0 * scale)

    # Filament glow when ON
    if is_on:
        painter.setPen(QPen(QColor("#ffffff"), 1.2 * scale))
        painter.drawLine(QPointF(14 * scale, 11 * scale), QPointF(16 * scale, 9 * scale))
        painter.drawLine(QPointF(16 * scale, 9 * scale), QPointF(18 * scale, 11 * scale))

    painter.end()
    return pixmap


class WorkerSignals(QObject):
    command_finished = Signal(dict)


class LampTask(QRunnable):
    """QRunnable task safely executed by QThreadPool."""
    def __init__(self, lamp: LampDevice, action: str, **kwargs):
        super().__init__()
        self.lamp = lamp
        self.action = action
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        result_state = {}
        try:
            if self.action == "toggle":
                self.lamp.toggle()
            elif self.action == "turn_on":
                self.lamp.turn_on()
            elif self.action == "turn_off":
                self.lamp.turn_off()
            elif self.action == "set_brightness":
                self.lamp.set_brightness(self.kwargs.get("level", 50))
            elif self.action == "set_color_temp":
                self.lamp.set_color_temp(self.kwargs.get("temp", 50))
            elif self.action == "set_rgb":
                r, g, b = self.kwargs.get("rgb", (255, 255, 255))
                self.lamp.set_rgb(r, g, b)
            elif self.action == "apply_preset":
                self.lamp.apply_preset(
                    self.kwargs.get("brightness", 50),
                    self.kwargs.get("color_temp", 50),
                )
            elif self.action == "refresh":
                self.lamp.refresh_status()

            result_state = self.lamp.get_state_dict()
        except Exception as e:
            result_state = self.lamp.get_state_dict()
            result_state["last_error"] = str(e)
            result_state["is_online"] = False

        try:
            self.signals.command_finished.emit(result_state)
        except RuntimeError:
            pass


class PopupPanel(QWidget):
    """
    Apple HomeKit inspired floating glass panel.
    Controls multi-devices, RGB colors, color temp, and scene presets.
    """

    def __init__(self, manager: DeviceManager, tray_app, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.tray_app = tray_app
        self.last_hide_timestamp = 0.0
        self._active_tasks = set()

        self._init_window_flags()
        self._init_ui()
        self.update_ui_state(self.manager.current.get_state_dict())

    @property
    def lamp(self) -> LampDevice:
        return self.manager.current

    def _init_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(theme.PANEL_WIDTH, theme.PANEL_HEIGHT)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)

        # Main Obsidian Glass Card
        self.card = QFrame(self)
        self.card.setObjectName("ContainerFrame")
        self.card.setStyleSheet(theme.get_panel_stylesheet())

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(theme.SHADOW_BLUR_RADIUS)
        shadow.setOffset(theme.SHADOW_OFFSET_X, theme.SHADOW_OFFSET_Y)
        shadow.setColor(theme.SHADOW_COLOR)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        # 1. Top Bar: HomeCTRL Title + Master All Off Action
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        app_title = QLabel("🏠 HomeCTRL", self.card)
        app_title.setFont(theme.FONT_HERO)

        self.all_off_btn = QPushButton("⏻ All Off", self.card)
        self.all_off_btn.setProperty("class", "action-pill")
        self.all_off_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.all_off_btn.clicked.connect(self._on_all_off_clicked)

        top_bar.addWidget(app_title)
        top_bar.addStretch()
        top_bar.addWidget(self.all_off_btn)
        card_layout.addLayout(top_bar)

        # 2. Multi-Device Segmented Bar
        self.device_tabs_layout = QHBoxLayout()
        self.device_tabs_layout.setSpacing(6)
        self.device_tab_btns = []

        device_bar = QFrame(self.card)
        device_bar.setObjectName("SegmentBar")
        dev_bar_layout = QHBoxLayout(device_bar)
        dev_bar_layout.setContentsMargins(4, 4, 4, 4)
        dev_bar_layout.setSpacing(4)

        for idx, dev in enumerate(self.manager.devices):
            btn = QPushButton(dev.name, device_bar)
            btn.setProperty("class", "segment-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "true" if idx == self.manager.active_index else "false")
            btn.clicked.connect(lambda _, i=idx: self._on_switch_device(i))
            dev_bar_layout.addWidget(btn)
            self.device_tab_btns.append(btn)

        card_layout.addWidget(device_bar)

        # 3. Hero Device Card (Apple Home Squircle Tile)
        hero_card = QFrame(self.card)
        hero_card.setObjectName("DeviceCard")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(14, 14, 14, 14)
        hero_layout.setSpacing(12)

        # Bulb Vector Glow Icon
        self.hero_icon = QLabel(hero_card)
        self.hero_icon.setFixedSize(38, 38)
        self.hero_icon.setPixmap(create_lamp_pixmap(size=38, is_on=False))
        hero_layout.addWidget(self.hero_icon)

        # Info
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

        # Large HomeKit Power Toggle
        self.power_btn = QPushButton(hero_card)
        self.power_btn.setFixedSize(48, 48)
        self.power_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power_btn.setText("⏻")
        self.power_btn.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
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
        for idx, (m_id, m_label) in enumerate([("white", "💡 White"), ("color", "🎨 Colors"), ("scenes", "✨ Scenes")]):
            btn = QPushButton(m_label, mode_bar)
            btn.setProperty("class", "segment-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda _, i=idx: self._on_switch_mode(i))
            mode_layout.addWidget(btn)
            self.mode_btns.append(btn)

        card_layout.addWidget(mode_bar)

        # 5. Stacked Pages (White, Colors, Scenes)
        self.stack = QStackedWidget(self.card)

        # Page 1: White Mode (Brightness + Color Temp)
        self.white_page = self._build_white_page()
        self.stack.addWidget(self.white_page)

        # Page 2: Colors Mode (Brightness + 16M Color Swatches + Color Wheel)
        self.colors_page = self._build_colors_page()
        self.stack.addWidget(self.colors_page)

        # Page 3: Scenes Mode (6 HomeKit Scenes)
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

        # Brightness Slider
        b_header = QHBoxLayout()
        b_title = QLabel("☀️ Brightness", page)
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
        self.minus_btn = QPushButton("−", page)
        self.minus_btn.setProperty("class", "step-button")
        self.minus_btn.setFixedSize(30, 30)
        self.minus_btn.clicked.connect(self._on_minus_clicked)

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal, page)
        self.brightness_slider.setObjectName("BrightnessSlider")
        self.brightness_slider.setRange(10, 100)
        self.brightness_slider.setValue(self.lamp.brightness)
        self.brightness_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.brightness_slider.valueChanged.connect(self._on_slider_value_changed)
        self.brightness_slider.sliderReleased.connect(self._commit_slider_brightness)

        self.plus_btn = QPushButton("+", page)
        self.plus_btn.setProperty("class", "step-button")
        self.plus_btn.setFixedSize(30, 30)
        self.plus_btn.clicked.connect(self._on_plus_clicked)

        b_row.addWidget(self.minus_btn)
        b_row.addWidget(self.brightness_slider)
        b_row.addWidget(self.plus_btn)
        layout.addLayout(b_row)

        # Color Temperature Slider
        t_header = QHBoxLayout()
        t_title = QLabel("🌡️ Color Temperature", page)
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
        self.warm_btn = QPushButton("🔥", page)
        self.warm_btn.setProperty("class", "step-button")
        self.warm_btn.setFixedSize(30, 30)
        self.warm_btn.clicked.connect(lambda: self._step_color_temp(-15))

        self.temp_slider = QSlider(Qt.Orientation.Horizontal, page)
        self.temp_slider.setObjectName("TempSlider")
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(self.lamp.color_temp)
        self.temp_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.temp_slider.valueChanged.connect(self._on_temp_value_changed)
        self.temp_slider.sliderReleased.connect(self._commit_temp_slider)

        self.cool_btn = QPushButton("❄️", page)
        self.cool_btn.setProperty("class", "step-button")
        self.cool_btn.setFixedSize(30, 30)
        self.cool_btn.clicked.connect(lambda: self._step_color_temp(15))

        t_row.addWidget(self.warm_btn)
        t_row.addWidget(self.temp_slider)
        t_row.addWidget(self.cool_btn)
        layout.addLayout(t_row)

        return page

    def _build_colors_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(12)

        swatch_title = QLabel("Color Palette (16M Colors)", page)
        swatch_title.setFont(theme.FONT_BOLD)
        layout.addWidget(swatch_title)

        grid = QGridLayout()
        grid.setSpacing(8)

        for idx, swatch in enumerate(theme.COLOR_SWATCHES):
            row = idx // 4
            col = idx % 4
            btn = QPushButton(page)
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(swatch["name"])
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {swatch['hex']};
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    border-color: #ffffff;
                    transform: scale(1.1);
                }}
                """
            )
            btn.clicked.connect(lambda _, c=swatch["rgb"]: self._on_color_picked(c))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        # Custom RGB Color Wheel / Dialog Button
        custom_color_btn = QPushButton("🎨 Custom Color Wheel...", page)
        custom_color_btn.setProperty("class", "action-pill")
        custom_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_color_btn.setFixedHeight(34)
        custom_color_btn.clicked.connect(self._on_open_color_dialog)
        layout.addWidget(custom_color_btn)

        return page

    def _build_scenes_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        for idx, sc in enumerate(theme.SCENES):
            row = idx // 2
            col = idx % 2
            btn = QPushButton(page)
            btn.setProperty("class", "scene-tile")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(8, 6, 8, 6)
            btn_layout.setSpacing(8)

            icon_lbl = QLabel(sc["icon"], btn)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 14))

            col_layout = QVBoxLayout()
            col_layout.setSpacing(1)
            name_lbl = QLabel(sc["label"], btn)
            name_lbl.setFont(theme.FONT_BOLD)
            desc_lbl = QLabel(sc["desc"], btn)
            desc_lbl.setFont(theme.FONT_SMALL)
            desc_lbl.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")

            col_layout.addWidget(name_lbl)
            col_layout.addWidget(desc_lbl)

            dot = QLabel(btn)
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background-color: {sc['color_hint']}; border-radius: 4px;")

            btn_layout.addWidget(icon_lbl)
            btn_layout.addLayout(col_layout)
            btn_layout.addStretch()
            btn_layout.addWidget(dot)

            btn.clicked.connect(lambda _, s=sc: self._on_scene_clicked(s))
            layout.addWidget(btn, row, col)

        return page

    def _set_status_dot_color(self, hex_color: str):
        self.footer_dot.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")

    def update_ui_state(self, state: dict):
        """Updates UI components to match active device state."""
        is_configured = state.get("is_configured", False)
        is_online = state.get("is_online", False)
        is_on = state.get("is_on", False)
        brightness = state.get("brightness", 50)
        color_temp = state.get("color_temp", 50)
        work_mode = state.get("work_mode", "white")
        rgb = state.get("rgb", (245, 158, 11))
        active_chan = state.get("active_channel", "cloud")

        self.hero_title.setText(self.lamp.name)

        # Update hero icon with dynamic color
        if is_on:
            self.hero_icon.setPixmap(create_lamp_pixmap(size=38, is_on=True, rgb=rgb if work_mode == "colour" else (245, 158, 11)))
        else:
            self.hero_icon.setPixmap(create_lamp_pixmap(size=38, is_on=False))

        # Power Button style
        if is_on:
            self.power_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {theme.POWER_ON_BG};
                    color: {theme.POWER_ON_FG};
                    border: 2px solid {theme.POWER_ON_BORDER};
                    border-radius: 24px;
                }}
                QPushButton:hover {{
                    background-color: {theme.ACCENT_AMBER_HOVER};
                }}
                """
            )
        else:
            self.power_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {theme.POWER_OFF_BG};
                    color: {theme.POWER_OFF_FG};
                    border: 1px solid {theme.POWER_OFF_BORDER};
                    border-radius: 24px;
                }}
                QPushButton:hover {{
                    background-color: {theme.BG_CARD_HOVER};
                    color: {theme.TEXT_PRIMARY};
                }}
                """
            )

        # Status text & footer
        if not is_configured:
            self._set_status_dot_color(theme.STATUS_OFFLINE)
            self.hero_status.setText("Not configured")
            self.footer_label.setText("No device credentials")
        elif not is_online:
            self._set_status_dot_color(theme.STATUS_OFFLINE)
            self.hero_status.setText("Offline")
            self.footer_label.setText(f"Unable to reach {self.lamp.ip_address}")
        else:
            self._set_status_dot_color(theme.STATUS_ONLINE)
            chan_tag = "Cloud" if active_chan == "cloud" else "Local"
            self.hero_status.setText(f"Online ({chan_tag}) • {'On' if is_on else 'Off'} • {brightness}%")
            self.footer_label.setText(f"Channel: {chan_tag} (Deco 5 GHz Mesh Active)")

        # Sliders (update only if not dragging)
        if not self.brightness_slider.isSliderDown():
            self.bright_val_label.setText(f"{brightness}%")
            self.brightness_slider.blockSignals(True)
            self.brightness_slider.setValue(brightness)
            self.brightness_slider.blockSignals(False)

        if not self.temp_slider.isSliderDown():
            self.temp_slider.blockSignals(True)
            self.temp_slider.setValue(color_temp)
            self.temp_slider.blockSignals(False)
            self._update_temp_label(color_temp)

        # Update tray icon
        self.tray_app.update_tray_state(is_on if is_online else False, rgb if work_mode == "colour" else (245, 158, 11))

    def _update_temp_label(self, val: int):
        if val < 25:
            self.temp_val_label.setText("Warm Candle (~2700K)")
        elif val < 60:
            self.temp_val_label.setText("Neutral (~4000K)")
        elif val < 85:
            self.temp_val_label.setText("Crisp White (~5000K)")
        else:
            self.temp_val_label.setText("Cool Daylight (~6500K)")

    def _run_worker(self, action: str, **kwargs):
        """Dispatches action safely to QThreadPool."""
        self._set_status_dot_color(theme.STATUS_BUSY)
        self.hero_status.setText("Connecting...")

        task = LampTask(self.lamp, action, **kwargs)
        self._active_tasks.add(task)

        def _on_done(result):
            self._active_tasks.discard(task)
            self.update_ui_state(result)

        task.signals.command_finished.connect(_on_done)
        QThreadPool.globalInstance().start(task)

    def _on_switch_device(self, index: int):
        self.manager.set_active(index)
        for idx, btn in enumerate(self.device_tab_btns):
            btn.setProperty("active", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.update_ui_state(self.lamp.get_state_dict())
        self._run_worker("refresh")

    def _on_switch_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        for idx, btn in enumerate(self.mode_btns):
            btn.setProperty("active", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_all_off_clicked(self):
        for dev in self.manager.devices:
            task = LampTask(dev, "turn_off")
            self._active_tasks.add(task)
            task.signals.command_finished.connect(lambda res: self._active_tasks.discard(task))
            QThreadPool.globalInstance().start(task)
        self.update_ui_state({"is_configured": True, "is_online": True, "is_on": False, "brightness": self.lamp.brightness})

    def _on_power_clicked(self):
        self._run_worker("toggle")

    def _on_slider_value_changed(self, value: int):
        self.bright_val_label.setText(f"{value}%")

    def _commit_slider_brightness(self):
        value = self.brightness_slider.value()
        self._run_worker("set_brightness", level=value)

    def _on_minus_clicked(self):
        cur = self.brightness_slider.value()
        new_val = max(10, cur - 10)
        self.brightness_slider.setValue(new_val)
        self._commit_slider_brightness()

    def _on_plus_clicked(self):
        cur = self.brightness_slider.value()
        new_val = min(100, cur + 10)
        self.brightness_slider.setValue(new_val)
        self._commit_slider_brightness()

    def _on_temp_value_changed(self, value: int):
        self._update_temp_label(value)

    def _commit_temp_slider(self):
        value = self.temp_slider.value()
        self._run_worker("set_color_temp", temp=value)

    def _step_color_temp(self, delta: int):
        cur = self.temp_slider.value()
        new_val = max(0, min(100, cur + delta))
        self.temp_slider.setValue(new_val)
        self._commit_temp_slider()

    def _on_color_picked(self, rgb: tuple):
        self._run_worker("set_rgb", rgb=rgb)

    def _on_open_color_dialog(self):
        color = QColorDialog.getColor(QColor(245, 158, 11), self, "Select Lamp RGB Color")
        if color.isValid():
            rgb = (color.red(), color.green(), color.blue())
            self._on_color_picked(rgb)

    def _on_scene_clicked(self, scene_data: dict):
        if "rgb" in scene_data:
            self._run_worker("set_rgb", rgb=scene_data["rgb"])
        else:
            self._run_worker(
                "apply_preset",
                brightness=scene_data["brightness"],
                color_temp=scene_data["color_temp"],
            )

    def show_anchored(self):
        screen = QApplication.primaryScreen()
        if not screen:
            self.show()
            return
        avail = screen.availableGeometry()
        x = avail.right() - theme.PANEL_WIDTH - theme.PANEL_MARGIN_RIGHT + 14
        y = avail.bottom() - theme.PANEL_HEIGHT - 8
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

        if self.lamp.is_configured:
            self._run_worker("refresh")

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                if hasattr(self, "brightness_slider") and self.brightness_slider.isSliderDown():
                    return
                if hasattr(self, "temp_slider") and self.temp_slider.isSliderDown():
                    return
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                if self.rect().contains(cursor_pos):
                    return
                self.hide()
        super().changeEvent(event)

    def hideEvent(self, event):
        self.last_hide_timestamp = time.time()
        super().hideEvent(event)


class TrayApp(QSystemTrayIcon):
    """System tray icon and menu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = get_device_manager()
        self.popup = PopupPanel(self.manager, self)

        self.setIcon(create_tray_icon())
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

        self.autostart_action = QAction("Start with Windows", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_autostart_enabled())
        self.autostart_action.triggered.connect(self._on_autostart_toggled)
        menu.addAction(self.autostart_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_show_clicked(self):
        self.popup.show_anchored()

    def _on_autostart_toggled(self, checked: bool):
        success = set_autostart_enabled(checked)
        if not success:
            self.autostart_action.setChecked(is_autostart_enabled())

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.popup.isVisible():
                self.popup.hide()
            else:
                if time.time() - self.popup.last_hide_timestamp < 0.25:
                    return
                self.popup.show_anchored()

    def update_tray_state(self, is_on: bool, rgb: tuple = (245, 158, 11)):
        self.setIcon(QIcon(create_lamp_pixmap(size=32, is_on=is_on, rgb=rgb)))


def create_tray_icon() -> QIcon:
    return QIcon(create_lamp_pixmap(size=32, is_on=False))
