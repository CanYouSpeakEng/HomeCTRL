"""
theme.py - Apple HomeKit Inspired Commercial Theme for HomeCTRL.

All colors, dimensions, corner radiuses, and fonts are centralized here.
Crafted for a modern, high-end Apple HomeKit aesthetic with frosted glass,
squircle cards, smooth capsule sliders, and vibrant color palettes.
"""

from PySide6.QtGui import QColor, QFont

# --- WINDOW & PANEL DIMENSIONS ---
PANEL_WIDTH = 370
PANEL_HEIGHT = 610
PANEL_MARGIN_BOTTOM = 48  # Spacing above Windows taskbar
PANEL_MARGIN_RIGHT = 18   # Spacing from right screen edge
CORNER_RADIUS = 22        # HomeKit smooth squircle curvature

# --- DROP SHADOW EFFECTS ---
SHADOW_BLUR_RADIUS = 36
SHADOW_OFFSET_X = 0
SHADOW_OFFSET_Y = 8
SHADOW_COLOR = QColor(0, 0, 0, 180)

# --- HOMEKIT COLOR PALETTE (Dark Glass Modern) ---
# Backgrounds
BG_PANEL = "#111317"          # Deep Midnight Obsidian
BG_CARD = "#1a1d24"           # Frosted glass card
BG_CARD_HOVER = "#242832"     # Subtle card hover
BG_SEGMENT = "#16181f"        # Recessed segmented pill bar
BG_INPUT = "#1e2129"          # Track background
BORDER_GLASS = "#282d38"      # Subtle glass border
BORDER_ACTIVE = "#f59e0b"     # Amber focus border

# Text
TEXT_PRIMARY = "#f8fafc"      # Clean white
TEXT_SECONDARY = "#94a3b8"    # Soft slate gray
TEXT_MUTED = "#64748b"        # Muted caption gray

# Accent Glows & Power States
ACCENT_AMBER = "#f59e0b"
ACCENT_AMBER_HOVER = "#fbbf24"
APPLE_YELLOW = "#ffd60a"      # Signature Apple Home tile yellow
APPLE_BLUE = "#0a84ff"
APPLE_GREEN = "#30d158"

POWER_ON_BG = "#ffd60a"       # Apple Home yellow when ON
POWER_ON_FG = "#0f1115"
POWER_ON_BORDER = "#eab308"
POWER_OFF_BG = "#222630"      # Sleek slate when OFF
POWER_OFF_FG = "#64748b"
POWER_OFF_BORDER = "#2e3442"

STATUS_ONLINE = "#30d158"     # Apple Green
STATUS_OFFLINE = "#ff453a"    # Apple Red
STATUS_BUSY = "#ffd60a"       # Apple Yellow

# --- FONTS ---
FONT_FAMILY = "Segoe UI"
FONT_HERO = QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
FONT_TITLE = QFont(FONT_FAMILY, 11, QFont.Weight.DemiBold)
FONT_BODY = QFont(FONT_FAMILY, 10, QFont.Weight.Normal)
FONT_BOLD = QFont(FONT_FAMILY, 10, QFont.Weight.DemiBold)
FONT_SMALL = QFont(FONT_FAMILY, 9, QFont.Weight.Normal)

# --- SLIDERS ---
SLIDER_HEIGHT = 10
SLIDER_HANDLE_SIZE = 22
BRIGHTNESS_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #78350f, stop:0.5 #d97706, stop:1 #fde68a)"
TEMP_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:0.4 #fde047, stop:0.7 #f8fafc, stop:1 #38bdf8)"

# --- QUICK-PICK 16-MILLION COLOR SWATCHES ---
COLOR_SWATCHES = [
    {"name": "Warm White",   "rgb": (255, 235, 180), "hex": "#ffebb4"},
    {"name": "Cool Daylight", "rgb": (230, 245, 255), "hex": "#e6f5ff"},
    {"name": "Sunset Amber", "rgb": (255, 140, 0),   "hex": "#ff8c00"},
    {"name": "Crimson",      "rgb": (239, 68, 68),   "hex": "#ef4444"},
    {"name": "Cyber Cyan",   "rgb": (6, 182, 212),   "hex": "#06b6d4"},
    {"name": "Neon Violet",  "rgb": (168, 85, 247),  "hex": "#a855f7"},
    {"name": "Emerald",      "rgb": (16, 185, 129),  "hex": "#10b981"},
    {"name": "Bubblegum",    "rgb": (244, 63, 94),   "hex": "#f43f5e"},
]

# --- BESPOKE SCENES (Dynamic Firmware Loops + Static Atmospheric Presets) ---
SCENES = [
    {
        "id": "aurora_wave",
        "label": "Aurora Flow",
        "icon_key": "wave",
        "type": "dynamic",
        "color_hint": "#00c7be",
        "desc": "6-Color Spectrum",
    },
    {
        "id": "ocean_breath",
        "label": "Ocean Breath",
        "icon_key": "breath",
        "type": "dynamic",
        "color_hint": "#0a84ff",
        "desc": "Respiration Loop",
    },
    {
        "id": "neon_pulse",
        "label": "Neon Pulse",
        "icon_key": "breath",
        "type": "dynamic",
        "color_hint": "#bf5af2",
        "desc": "Violet & Magenta",
    },
    {
        "id": "amber_hearth",
        "label": "Amber Hearth",
        "icon_key": "candle",
        "type": "dynamic",
        "color_hint": "#ff9500",
        "desc": "Flame Glow",
    },
    {
        "id": "disco_jump",
        "label": "Party Pulse",
        "icon_key": "disco",
        "type": "dynamic",
        "color_hint": "#ff3b30",
        "desc": "Rhythmic Jump",
    },
    {
        "id": "reading",
        "label": "Paper Read",
        "icon_key": "read",
        "type": "static",
        "color_hint": "#f59e0b",
        "desc": "85% • 4000K Neutral",
    },
    {
        "id": "focus",
        "label": "Studio Focus",
        "icon_key": "focus",
        "type": "static",
        "color_hint": "#38bdf8",
        "desc": "100% • 6000K Daylight",
    },
    {
        "id": "midnight",
        "label": "Midnight Glow",
        "icon_key": "night",
        "type": "static",
        "color_hint": "#818cf8",
        "desc": "12% • Dim Amber",
    },
]


def get_panel_stylesheet() -> str:
    """Returns HomeKit glass card stylesheet."""
    return f"""
    #ContainerFrame {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER_GLASS};
        border-radius: {CORNER_RADIUS}px;
    }}

    QLabel {{
        color: {TEXT_PRIMARY};
        font-family: "{FONT_FAMILY}";
    }}

    /* Device Card Squircle */
    #DeviceCard {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_GLASS};
        border-radius: 18px;
    }}

    /* Segmented Tab Bar */
    #SegmentBar {{
        background-color: {BG_SEGMENT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 3px;
    }}
    QPushButton.segment-btn {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: 9px;
        padding: 6px 14px;
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
        font-weight: bold;
    }}
    QPushButton.segment-btn:hover {{
        color: #ffffff;
    }}
    QPushButton.segment-btn[active="true"] {{
        background-color: {BG_CARD_HOVER};
        color: {TEXT_PRIMARY};
        border: 1px solid rgba(255, 255, 255, 0.12);
    }}

    /* Step Plus/Minus Buttons */
    QPushButton.step-button {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_GLASS};
        border-radius: 16px;
        font-family: "{FONT_FAMILY}";
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton.step-button:hover {{
        background-color: {BG_CARD_HOVER};
        border-color: {ACCENT_AMBER};
        color: #ffffff;
    }}
    QPushButton.step-button:pressed {{
        background-color: {BG_PANEL};
    }}

    /* Brightness Gradient Slider */
    QSlider#BrightnessSlider::groove:horizontal {{
        height: {SLIDER_HEIGHT}px;
        border-radius: {SLIDER_HEIGHT // 2}px;
        background: {BRIGHTNESS_GRADIENT};
    }}
    QSlider#BrightnessSlider::handle:horizontal {{
        background-color: #ffffff;
        border: 3px solid {ACCENT_AMBER};
        width: {SLIDER_HANDLE_SIZE}px;
        height: {SLIDER_HANDLE_SIZE}px;
        margin: -{((SLIDER_HANDLE_SIZE - SLIDER_HEIGHT) // 2)}px 0;
        border-radius: {SLIDER_HANDLE_SIZE // 2}px;
    }}
    QSlider#BrightnessSlider::handle:horizontal:hover {{
        border-color: {ACCENT_AMBER_HOVER};
        background-color: #fefce8;
    }}

    /* Temperature Gradient Slider */
    QSlider#TempSlider::groove:horizontal {{
        height: {SLIDER_HEIGHT}px;
        border-radius: {SLIDER_HEIGHT // 2}px;
        background: {TEMP_GRADIENT};
    }}
    QSlider#TempSlider::handle:horizontal {{
        background-color: #ffffff;
        border: 3px solid #60a5fa;
        width: {SLIDER_HANDLE_SIZE}px;
        height: {SLIDER_HANDLE_SIZE}px;
        margin: -{((SLIDER_HANDLE_SIZE - SLIDER_HEIGHT) // 2)}px 0;
        border-radius: {SLIDER_HANDLE_SIZE // 2}px;
    }}
    QSlider#TempSlider::handle:horizontal:hover {{
        border-color: #93c5fd;
    }}

    /* HomeKit Scene Tile */
    QPushButton.scene-tile {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_GLASS};
        border-radius: 14px;
        padding: 10px 8px;
        text-align: left;
    }}
    QPushButton.scene-tile:hover {{
        background-color: {BG_CARD_HOVER};
        border-color: rgba(255, 255, 255, 0.2);
    }}
    QPushButton.scene-tile:pressed {{
        background-color: {BG_SEGMENT};
    }}

    /* Quick Action Header Buttons */
    QPushButton.action-pill {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    QPushButton.action-pill:hover {{
        background-color: {BG_CARD_HOVER};
        border-color: rgba(255, 255, 255, 0.25);
    }}
    """
