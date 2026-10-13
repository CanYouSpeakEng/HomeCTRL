# HomeCTRL

> **Commercial-Grade Smart Lighting Control for Windows with Apple HomeKit Aesthetics.**

HomeCTRL is a modern Windows system tray utility crafted with Python and PySide6. It brings the refined, minimalist design of Apple HomeKit to your Windows desktop, providing near-instant control over BARDI, Tuya, and SmartLife Wi-Fi smart bulbs and LED light strips.

100% bespoke design: **zero generic emojis, zero stock raster icons, and zero standard OS dialogs.**

---

## Key Highlights

- **Apple HomeKit Aesthetics**:
  - Dark glassmorphism card with rounded squircle tiles and soft borders.
  - Interactive glowing device hero tile with live brightness and power indicators.
  - Segmented pill navigation (White, Colors, Scenes).
- **Pure Bespoke Vector Icons**:
  - Every icon is mathematically drawn with resolution-independent vector paths (QPainter / QPainterPath).
  - No generic Unicode emojis anywhere in the interface.
- **Custom Interactive Color Wheel**:
  - Custom-engineered 360-degree Hue-Saturation conical disc.
  - Interactive lens dragger pin with real-time RGB and Hex readouts.
  - 8 curated quick-tap color swatches.
  - No generic OS color dialogs.
- **Hardware Dynamic Scenes**:
  - **Aurora Flow**: Continuous smooth 6-color RGB gradient loop (firmware-rendered).
  - **Ocean Breath**: Calming deep cobalt to cyan respiration loop.
  - **Neon Pulse**: Electric violet and magenta pulse.
  - **Amber Hearth**: Fireplace flame breathing glow.
  - **Party Pulse**: High-energy rhythmic RGB step cycle.
  - **Atmospheric Static**: Paper Read (4000K), Studio Focus (6000K), Midnight Glow (2000K).
- **Tactile Haptic Sound Design**:
  - Custom-synthesized 44.1 kHz 16-bit PCM WAV feedback:
    - Airy panel entrance & dismissal swooshes.
    - Tactile resonant switch clicks on power toggle.
    - Sub-millisecond tactile ticks on sliders and color adjustments.
  - Built-in one-click sound mute toggle.
- **Fluid Spring Animations**:
  - Smooth slide-up and fade-in entrance when launched from tray.
  - Smooth slide-down dismissal animation.
- **Hybrid Dual-Engine Routing**:
  - **Local LAN Direct**: Connects locally over TCP port 6668 for zero-latency, sub-50ms offline response.
  - **Automatic Cloud Fallback**: Automatically routes via Tuya Cloud API (~300ms) if cross-band isolation on mesh Wi-Fi (e.g. Deco 5 GHz <-> 2.4 GHz) blocks local unicast.
- **Lightweight Windows Tray Native**:
  - Anchored to the bottom-right taskbar near the system clock.
  - Dismisses automatically on outside click.
  - Windows Startup toggle to launch silently on boot.
  - Self-contained single-file executable (`HomeCTRL.exe`).

---

## Project Architecture

```
HomeCTRL/
├── assets/               # High-res vector icons and synthesized audio
│   ├── app_icon.ico
│   ├── app_icon.png
│   └── sounds/           # 44.1 kHz 16-bit WAV tactile sounds
├── color_wheel.py        # Custom Hue-Saturation color disc widget
├── icons.py              # Mathematical vector icon rendering engine
├── sound.py              # Low-latency asynchronous winsound audio player
├── sound_gen.py          # Pure Python audio synthesizer
├── lamp.py               # Hardware abstraction layer (Local TinyTuya + Cloud Fallback)
├── theme.py              # HomeKit colors, typography, and QSS design system
├── ui.py                 # PySide6 popup card, animations, and system tray
├── main.py               # Application entry point & tray icon
├── setup_device.py       # Cloud linking & device credential wizard
├── config.example.json   # Template for device configurations
├── install.ps1           # 1-Click native Windows installer
└── build_exe.py          # PyInstaller packaging automation
```

---

## Quick Start Guide

### 1. Requirements
- Windows 10 or 11 (64-bit)
- Python 3.11+ (if running from source)

### 2. Installation (From Source)

```powershell
# Clone the repository
git clone https://github.com/CanYouSpeakEng/HomeCTRL.git
cd HomeCTRL

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Device Configuration
Copy the template configuration file:
```powershell
copy config.example.json config.json
```

Run the setup wizard to fetch your local keys automatically via your Tuya IoT Developer account:
```powershell
python setup_device.py
```

### 4. Run the Application
```powershell
python main.py
```

- **Left-click** the system tray icon to reveal the HomeKit control card.
- **Right-click** for the context menu (Show, Sound Effects, Start with Windows, Quit).

---

## Standalone Executable Build

To compile `HomeCTRL` as a single standalone `.exe` without requiring Python:

```powershell
python build_exe.py
```

The compiled binary will be located at:
```
dist/HomeCTRL.exe
```

---

## Privacy & Security
HomeCTRL stores device IDs, API secrets, and encryption keys strictly on your local machine in `config.json`. No telemetry or data is ever collected or sent to third-party analytics servers.

---

## License
MIT License.
