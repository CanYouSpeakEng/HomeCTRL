# HomeCTRL 💡

> **Commercial-Grade Smart Lighting Control for Windows with Apple HomeKit Aesthetics.**

**HomeCTRL** is a sleek, modern Windows system tray utility crafted with Python and PySide6. It brings the refined, minimalist design of Apple HomeKit to your Windows desktop, providing near-instant control over BARDI, Tuya, and SmartLife Wi-Fi smart bulbs and LED light strips.

---

## ✨ Features

- ** Apple HomeKit Aesthetic**:
  - Dark glassmorphism card with rounded squircle tiles and soft borders.
  - Interactive glowing device hero tile with live brightness and power indicators.
  - Fluid segmented pill navigation (`White`, `Colors`, `Scenes`).
- **🌈 Full Spectrum 16 Million RGB Colors**:
  - 8 curated quick-tap swatches (Warm Amber, Sunset Red, Electric Blue, Emerald Green, Cyberpunk Purple, and more).
  - Built-in full-spectrum color picker dialog for custom RGB HEX/HSV selection.
- **☀️ Continuous Color Temperature (2700K – 6500K)**:
  - Natural sunlight gradient slider for continuous Kelvin temperature adjustments.
  - Smooth brightness slider with step buttons (`−` and `+`).
- **🎭 Quick Scene Presets**:
  - 6 lighting scenes: **Reading**, **Relax**, **Focus**, **Night**, **Party**, and **Cinema**.
- **🔀 Multi-Device Switcher & Master Actions**:
  - Switch seamlessly between lights (e.g. `Light 1 (Bulb)`, `Desk (Strip)`).
  - Quick **"All Off"** master toggle to blackout your room in one click.
- **⚡ Hybrid Dual-Engine Routing**:
  - **Local LAN Direct**: Connects locally over TCP port 6668 for zero-latency, sub-50ms offline response.
  - **Automatic Cloud Fallback**: Automatically routes via Tuya Cloud API (~300ms) if cross-band isolation on mesh Wi-Fi (e.g. Deco 5 GHz ↔ 2.4 GHz) blocks local unicast.
- **🚀 Lightweight Windows Tray Native**:
  - Anchored to the bottom-right taskbar near the system clock.
  - Dismisses automatically on outside click.
  - Windows Startup toggle to launch silently on boot.
  - Runs in background with virtually 0% CPU and low memory footprint.

---

## 🛠️ Project Architecture

```
HomeCTRL/
├── assets/               # High-res application icons (PNG, ICO)
├── lamp.py               # Hardware abstraction layer (Local TinyTuya + Cloud Fallback)
├── theme.py              # HomeKit colors, typography, and QSS design system
├── ui.py                 # PySide6 popup card, custom sliders, RGB swatches
├── main.py               # Application entry point & tray icon
├── setup_device.py       # Cloud linking & device credential wizard
├── config.example.json   # Template for device configurations
└── build_exe.py          # PyInstaller packaging automation
```

---

## 🚀 Quick Start Guide

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
- **Right-click** for the context menu (Open, Start with Windows, Quit).

---

## 📦 Standalone Executable Build

To package `HomeCTRL` as a single standalone `.exe` without requiring Python:

```powershell
python build_exe.py
```

The compiled binary will be located at:
```
dist/HomeCTRL.exe
```

---

## 🛡️ Privacy & Security
`HomeCTRL` stores device IDs, API secrets, and encryption keys strictly on your local machine in `config.json`. **No telemetry or data is ever collected or sent to third-party analytics servers.**

---

## 📄 License
MIT License. Crafted for clean, distraction-free home automation.
