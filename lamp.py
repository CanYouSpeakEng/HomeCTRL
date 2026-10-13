"""
lamp.py - Tuya Device Communication Layer for Smart Lamps & Light Strips.

Features:
- Hybrid Local Wi-Fi + Tuya Cloud fallback (zero delay, mesh-friendly).
- Full White mode (Brightness 10-100% and Color Temperature 0-100%).
- Full 16-Million Color RGB mode (converts RGB to Tuya HSV colour_data_v2).
- Multi-device support: controls Light 1, Desk Strip, or All Lights.
"""

import sys
import os
import json
import time
import colorsys
import logging
from typing import Optional, Dict, Any, List

try:
    import tinytuya
except ImportError:
    tinytuya = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HomeCTRL.Lamp")


def get_config_path() -> str:
    """Finds config.json across executable folder, AppData, working dir, or dev tree."""
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "config.json"))
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        candidates.append(os.path.join(localapp, "HomeCTRL", "config.json"))
    candidates.append(os.path.join(os.getcwd(), "config.json"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))

    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0] if candidates else "config.json"


def get_tinytuya_config_path() -> str:
    """Finds tinytuya.json across executable folder, AppData, working dir, or dev tree."""
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "tinytuya.json"))
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        candidates.append(os.path.join(localapp, "HomeCTRL", "tinytuya.json"))
    candidates.append(os.path.join(os.getcwd(), "tinytuya.json"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tinytuya.json"))

    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0] if candidates else "tinytuya.json"


CONFIG_PATH = get_config_path()
TINYTUYA_CONFIG_PATH = get_tinytuya_config_path()


def load_cloud_credentials() -> Optional[Dict[str, str]]:
    """Loads Tuya cloud API credentials from config.json or tinytuya.json."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            cloud = data.get("cloud", {})
            if cloud.get("api_key") and cloud.get("api_secret"):
                return {
                    "api_key": cloud["api_key"],
                    "api_secret": cloud["api_secret"],
                    "region": cloud.get("region", "us"),
                }
        except Exception:
            pass

    if os.path.exists(TINYTUYA_CONFIG_PATH):
        try:
            with open(TINYTUYA_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("apiKey") and data.get("apiSecret"):
                return {
                    "api_key": data["apiKey"],
                    "api_secret": data["apiSecret"],
                    "region": data.get("apiRegion", "us"),
                }
        except Exception:
            pass

    return None


SCENE_CATALOG: Dict[str, Dict[str, Any]] = {
    # --- Dynamic Animated Hardware Loops (Firmware-Rendered) ---
    "aurora_wave": {
        "id": "aurora_wave",
        "name": "Aurora Flow",
        "type": "dynamic",
        "desc": "Smooth 6-color spectrum flow",
        "icon": "wave",
        "accent": "#00c7be",
        "payload": {
            "scene_num": 8,
            "scene_units": [
                {"bright": 0, "temperature": 0, "h": 0, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
                {"bright": 0, "temperature": 0, "h": 60, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
                {"bright": 0, "temperature": 0, "h": 120, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
                {"bright": 0, "temperature": 0, "h": 180, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
                {"bright": 0, "temperature": 0, "h": 240, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
                {"bright": 0, "temperature": 0, "h": 300, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 60, "unit_switch_duration": 60},
            ]
        }
    },
    "ocean_breath": {
        "id": "ocean_breath",
        "name": "Ocean Breath",
        "type": "dynamic",
        "desc": "Deep cobalt & cyan respiration",
        "icon": "breath",
        "accent": "#0a84ff",
        "payload": {
            "scene_num": 5,
            "scene_units": [
                {"bright": 0, "temperature": 0, "h": 215, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 70, "unit_switch_duration": 70},
                {"bright": 0, "temperature": 0, "h": 185, "s": 950, "v": 150, "unit_change_mode": "gradient", "unit_gradient_duration": 70, "unit_switch_duration": 70},
            ]
        }
    },
    "neon_pulse": {
        "id": "neon_pulse",
        "name": "Neon Pulse",
        "type": "dynamic",
        "desc": "Electric violet & magenta pulse",
        "icon": "breath",
        "accent": "#bf5af2",
        "payload": {
            "scene_num": 5,
            "scene_units": [
                {"bright": 0, "temperature": 0, "h": 315, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 65, "unit_switch_duration": 65},
                {"bright": 0, "temperature": 0, "h": 270, "s": 1000, "v": 200, "unit_change_mode": "gradient", "unit_gradient_duration": 65, "unit_switch_duration": 65},
            ]
        }
    },
    "amber_hearth": {
        "id": "amber_hearth",
        "name": "Amber Hearth",
        "type": "dynamic",
        "desc": "Warm flame respiration glow",
        "icon": "candle",
        "accent": "#ff9500",
        "payload": {
            "scene_num": 5,
            "scene_units": [
                {"bright": 0, "temperature": 0, "h": 32, "s": 1000, "v": 1000, "unit_change_mode": "gradient", "unit_gradient_duration": 75, "unit_switch_duration": 75},
                {"bright": 0, "temperature": 0, "h": 24, "s": 1000, "v": 120, "unit_change_mode": "gradient", "unit_gradient_duration": 75, "unit_switch_duration": 75},
            ]
        }
    },
    "disco_jump": {
        "id": "disco_jump",
        "name": "Party Pulse",
        "type": "dynamic",
        "desc": "High-energy rhythmic RGB jump",
        "icon": "disco",
        "accent": "#ff3b30",
        "payload": {
            "scene_num": 7,
            "scene_units": [
                {"bright": 0, "temperature": 0, "h": 0, "s": 1000, "v": 1000, "unit_change_mode": "jump", "unit_gradient_duration": 20, "unit_switch_duration": 40},
                {"bright": 0, "temperature": 0, "h": 120, "s": 1000, "v": 1000, "unit_change_mode": "jump", "unit_gradient_duration": 20, "unit_switch_duration": 40},
                {"bright": 0, "temperature": 0, "h": 240, "s": 1000, "v": 1000, "unit_change_mode": "jump", "unit_gradient_duration": 20, "unit_switch_duration": 40},
                {"bright": 0, "temperature": 0, "h": 60, "s": 1000, "v": 1000, "unit_change_mode": "jump", "unit_gradient_duration": 20, "unit_switch_duration": 40},
            ]
        }
    },

    # --- Static Curated Lighting ---
    "reading": {
        "id": "reading",
        "name": "Paper Read",
        "type": "static",
        "desc": "85% Brightness • 4000K Neutral Balance",
        "icon": "read",
        "accent": "#f59e0b",
        "brightness": 85,
        "color_temp": 50,
    },
    "focus": {
        "id": "focus",
        "name": "Studio Focus",
        "type": "static",
        "desc": "100% Brightness • 6000K Daylight Alert",
        "icon": "focus",
        "accent": "#38bdf8",
        "brightness": 100,
        "color_temp": 100,
    },
    "midnight": {
        "id": "midnight",
        "name": "Midnight Glow",
        "type": "static",
        "desc": "12% Brightness • 2000K Candlelight",
        "icon": "night",
        "accent": "#818cf8",
        "brightness": 12,
        "color_temp": 0,
    },
}


class LampDevice:
    """
    Controls a single BARDI/Tuya smart lamp or LED strip.
    Supports On/Off, Brightness, Color Temperature, Full RGB, and Dynamic Scenes.
    """

    DPS_SWITCH = "20"
    DPS_MODE = "21"
    DPS_BRIGHTNESS = "22"
    DPS_COLORTEMP = "23"
    DPS_COLOUR_DATA = "24"
    DPS_SCENE = "25"

    def __init__(
        self,
        name: str = "BARDI Smart Lamp",
        device_id: str = "",
        local_key: str = "",
        ip_address: str = "",
        protocol_version: str = "3.3",
        device_type: str = "lamp",
        cloud_creds: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.device_id = device_id.strip() if device_id else ""
        self.local_key = local_key.strip() if local_key else ""
        self.ip_address = ip_address.strip() if ip_address else ""
        self.protocol_version = str(protocol_version).strip() if protocol_version else "3.3"
        self.device_type = device_type
        self.cloud_creds = cloud_creds or load_cloud_credentials()

        self._device: Optional[Any] = None
        self._cloud: Optional[Any] = None
        self._is_online: bool = False
        self._is_on: bool = False
        self._brightness: int = 50       # 10 to 100
        self._color_temp: int = 50       # 0 (warm) to 100 (cool)
        self._work_mode: str = "white"   # "white" or "colour"
        self._rgb: tuple = (255, 255, 255)
        self._last_error: str = ""
        self._is_configured: bool = False
        self._active_channel: str = "cloud"
        self._local_available: bool = False
        self._last_local_attempt: float = 0.0

        self._check_and_init()

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def color_temp(self) -> int:
        return self._color_temp

    @property
    def work_mode(self) -> str:
        return self._work_mode

    @property
    def rgb(self) -> tuple:
        return self._rgb

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def active_channel(self) -> str:
        return self._active_channel

    def _check_and_init(self):
        """Initializes device credentials and API handles."""
        if not self.device_id:
            self._is_configured = False
            self._is_online = False
            self._last_error = "Device ID missing."
            return

        self._is_configured = True

        if tinytuya and self.local_key and self.ip_address:
            try:
                ver = float(self.protocol_version) if self.protocol_version else 3.3
                self._device = tinytuya.BulbDevice(
                    dev_id=self.device_id,
                    address=self.ip_address,
                    local_key=self.local_key,
                    version=ver,
                )
                self._device.set_socketTimeout(1.2)
                self._device.set_socketRetryLimit(1)
            except Exception as e:
                logger.warning(f"Local device init: {e}")

        if tinytuya and self.cloud_creds:
            try:
                self._cloud = tinytuya.Cloud(
                    apiRegion=self.cloud_creds.get("region", "us"),
                    apiKey=self.cloud_creds.get("api_key", ""),
                    apiSecret=self.cloud_creds.get("api_secret", ""),
                    apiDeviceID=self.device_id,
                )
            except Exception as e:
                logger.warning(f"Cloud client init: {e}")

    def _should_try_local(self) -> bool:
        if not self._device or not self.ip_address:
            return False
        if self._local_available:
            return True
        return (time.time() - self._last_local_attempt) > 300.0

    def refresh_status(self) -> Dict[str, Any]:
        """Queries status from lamp (local first if available, then cloud)."""
        if not self._is_configured:
            return self.get_state_dict()

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.status()
                if isinstance(res, dict) and "dps" in res:
                    dps = res["dps"]
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    self._last_error = ""

                    if self.DPS_SWITCH in dps:
                        self._is_on = bool(dps[self.DPS_SWITCH])
                    if self.DPS_MODE in dps:
                        self._work_mode = str(dps[self.DPS_MODE])
                    if self.DPS_BRIGHTNESS in dps:
                        self._brightness = max(10, min(100, round(dps[self.DPS_BRIGHTNESS] / 10)))
                    if self.DPS_COLORTEMP in dps:
                        self._color_temp = max(0, min(100, round(dps[self.DPS_COLORTEMP] / 10)))
                    return self.get_state_dict()
            except Exception:
                self._local_available = False

        if self._cloud:
            try:
                res = self._cloud.getstatus(self.device_id)
                if isinstance(res, dict) and res.get("success") and "result" in res:
                    self._is_online = True
                    self._active_channel = "cloud"
                    self._last_error = ""

                    for item in res["result"]:
                        code = item.get("code")
                        val = item.get("value")
                        if code == "switch_led":
                            self._is_on = bool(val)
                        elif code == "work_mode":
                            self._work_mode = str(val)
                        elif code == "bright_value_v2" and isinstance(val, (int, float)):
                            self._brightness = max(10, min(100, round(val / 10)))
                        elif code == "temp_value_v2" and isinstance(val, (int, float)):
                            self._color_temp = max(0, min(100, round(val / 10)))
                        elif code == "colour_data_v2":
                            try:
                                c_obj = json.loads(val) if isinstance(val, str) else val
                                h = c_obj.get("h", 0) / 360.0
                                s = c_obj.get("s", 1000) / 1000.0
                                v = c_obj.get("v", 1000) / 1000.0
                                rgb = colorsys.hsv_to_rgb(h, s, v)
                                self._rgb = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                            except Exception:
                                pass

                    return self.get_state_dict()
                else:
                    self._is_online = False
                    self._last_error = str(res.get("msg", "Cloud error"))
            except Exception as e:
                self._is_online = False
                self._last_error = str(e)

        return self.get_state_dict()

    def _send_cloud_command(self, commands: list) -> bool:
        if not self._cloud:
            return False
        try:
            res = self._cloud.sendcommand(self.device_id, {"commands": commands})
            if isinstance(res, dict) and res.get("success"):
                self._is_online = True
                self._active_channel = "cloud"
                self._last_error = ""
                return True
            else:
                logger.error(f"Cloud command error: {res}")
                return False
        except Exception as e:
            logger.error(f"Cloud command error: {e}")
            return False

    def turn_on(self) -> bool:
        """Turns the device ON."""
        if not self._is_configured:
            return False

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.turn_on()
                if isinstance(res, dict) and "Error" not in res:
                    self._is_on = True
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    return True
            except Exception:
                self._local_available = False

        ok = self._send_cloud_command([{"code": "switch_led", "value": True}])
        if ok:
            self._is_on = True
        return ok

    def turn_off(self) -> bool:
        """Turns the device OFF."""
        if not self._is_configured:
            return False

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.turn_off()
                if isinstance(res, dict) and "Error" not in res:
                    self._is_on = False
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    return True
            except Exception:
                self._local_available = False

        ok = self._send_cloud_command([{"code": "switch_led", "value": False}])
        if ok:
            self._is_on = False
        return ok

    def toggle(self) -> bool:
        return self.turn_off() if self._is_on else self.turn_on()

    def set_brightness(self, level: int) -> bool:
        """Sets brightness from 10 to 100%."""
        if not self._is_configured:
            return False
        clamped = max(10, min(100, int(level)))
        tuya_val = clamped * 10

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.set_value(self.DPS_BRIGHTNESS, tuya_val)
                if isinstance(res, dict) and "Error" not in res:
                    self._brightness = clamped
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    return True
            except Exception:
                self._local_available = False

        ok = self._send_cloud_command([
            {"code": "work_mode", "value": "white"},
            {"code": "bright_value_v2", "value": tuya_val}
        ])
        if ok:
            self._brightness = clamped
            self._work_mode = "white"
        return ok

    def set_color_temp(self, temp: int) -> bool:
        """Sets color temperature from 0 (warm amber) to 100 (cool daylight)."""
        if not self._is_configured:
            return False
        clamped = max(0, min(100, int(temp)))
        tuya_val = clamped * 10

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.set_value(self.DPS_COLORTEMP, tuya_val)
                if isinstance(res, dict) and "Error" not in res:
                    self._color_temp = clamped
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    return True
            except Exception:
                self._local_available = False

        ok = self._send_cloud_command([
            {"code": "work_mode", "value": "white"},
            {"code": "temp_value_v2", "value": tuya_val}
        ])
        if ok:
            self._color_temp = clamped
            self._work_mode = "white"
        return ok

    def set_rgb(self, r: int, g: int, b: int) -> bool:
        """
        Sets full 16-million RGB color.
        Switches device to 'colour' mode and transmits colour_data_v2 payload.
        """
        if not self._is_configured:
            return False

        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        h_deg = int(h * 360)
        s_val = int(s * 1000)
        v_val = max(100, int(v * 1000))

        colour_json = json.dumps({"h": h_deg, "s": s_val, "v": v_val})

        if self._should_try_local():
            try:
                self._last_local_attempt = time.time()
                res = self._device.set_colour(r, g, b)
                if isinstance(res, dict) and "Error" not in res:
                    self._rgb = (r, g, b)
                    self._work_mode = "colour"
                    self._is_on = True
                    self._is_online = True
                    self._local_available = True
                    self._active_channel = "local"
                    return True
            except Exception:
                self._local_available = False

        commands = [
            {"code": "switch_led", "value": True},
            {"code": "work_mode", "value": "colour"},
            {"code": "colour_data_v2", "value": colour_json},
        ]
        ok = self._send_cloud_command(commands)
        if ok:
            self._rgb = (r, g, b)
            self._work_mode = "colour"
            self._is_on = True
        return ok

    def set_dynamic_scene(self, scene_payload: dict) -> bool:
        """Sets a dynamic hardware-animated scene (breathing, rainbow flow, pulse)."""
        if not self._is_configured:
            return False

        if self._cloud:
            commands = [
                {"code": "switch_led", "value": True},
                {"code": "work_mode", "value": "scene"},
                {"code": "scene_data_v2", "value": scene_payload},
            ]
            ok = self._send_cloud_command(commands)
            if ok:
                self._is_on = True
                self._work_mode = "scene"
                return True

        if self._should_try_local():
            try:
                self._device.set_multiple_values({
                    self.DPS_SWITCH: True,
                    self.DPS_MODE: "scene",
                    self.DPS_SCENE: json.dumps(scene_payload),
                })
                self._is_on = True
                self._work_mode = "scene"
                return True
            except Exception as e:
                logger.warning(f"Local set_dynamic_scene error: {e}")

        return False

    def apply_named_scene(self, scene_id: str) -> bool:
        """Applies a curated scene from SCENE_CATALOG by ID."""
        scene = SCENE_CATALOG.get(scene_id)
        if not scene:
            return False
        if scene.get("type") == "dynamic":
            return self.set_dynamic_scene(scene["payload"])
        else:
            return self.apply_preset(scene.get("brightness", 80), scene.get("color_temp", 50))

    def apply_preset(self, brightness: int, color_temp: int) -> bool:
        """Applies a preset scene (ensures white mode, brightness, and color temp)."""
        if not self._is_configured:
            return False

        b_clamped = max(10, min(100, int(brightness)))
        t_clamped = max(0, min(100, int(color_temp)))

        if self._cloud:
            commands = [
                {"code": "switch_led", "value": True},
                {"code": "work_mode", "value": "white"},
                {"code": "bright_value_v2", "value": b_clamped * 10},
                {"code": "temp_value_v2", "value": t_clamped * 10},
            ]
            ok = self._send_cloud_command(commands)
            if ok:
                self._is_on = True
                self._brightness = b_clamped
                self._color_temp = t_clamped
                self._work_mode = "white"
                return True

        self.turn_on()
        time.sleep(0.15)
        self.set_brightness(b_clamped)
        time.sleep(0.15)
        self.set_color_temp(t_clamped)
        return True

    def get_state_dict(self) -> Dict[str, Any]:
        """Returns snapshot of current device state."""
        return {
            "name": self.name,
            "device_id": self.device_id,
            "is_configured": self._is_configured,
            "is_online": self._is_online,
            "is_on": self._is_on,
            "brightness": self._brightness,
            "color_temp": self._color_temp,
            "work_mode": self._work_mode,
            "rgb": self._rgb,
            "active_channel": self._active_channel,
            "last_error": self._last_error,
        }


class DeviceManager:
    """Manages all lights and accessories configured in config.json."""

    def __init__(self, config_file: str = CONFIG_PATH):
        self.config_file = config_file
        self.devices: List[LampDevice] = []
        self.active_index: int = 0
        self.reload()

    def reload(self):
        self.devices = []
        if not os.path.exists(self.config_file):
            self.devices = [LampDevice(name="BARDI Smart Lamp")]
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cloud_creds = data.get("cloud")
            devices_list = data.get("devices", [])
            for d in devices_list:
                # Include lighting devices (bulb and light strip)
                dev_type = d.get("device_type", "lamp")
                name = d.get("name", "")
                if "Camera" in name or "Pintu" in name:
                    continue  # Filter out non-lighting devices

                dev = LampDevice(
                    name=name or "BARDI Smart Lamp",
                    device_id=d.get("device_id", ""),
                    local_key=d.get("local_key", ""),
                    ip_address=d.get("ip_address", ""),
                    protocol_version=d.get("protocol_version", "3.3"),
                    device_type=dev_type,
                    cloud_creds=cloud_creds,
                )
                self.devices.append(dev)

            if not self.devices:
                self.devices = [LampDevice(name="BARDI Smart Lamp", cloud_creds=cloud_creds)]
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            self.devices = [LampDevice(name="BARDI Smart Lamp")]

    @property
    def current(self) -> LampDevice:
        if not self.devices:
            return LampDevice(name="BARDI Smart Lamp")
        idx = max(0, min(len(self.devices) - 1, self.active_index))
        return self.devices[idx]

    def set_active(self, index: int):
        if 0 <= index < len(self.devices):
            self.active_index = index

    def turn_all_off(self):
        for d in self.devices:
            d.turn_off()

    def turn_all_on(self):
        for d in self.devices:
            d.turn_on()


_GLOBAL_MANAGER: Optional[DeviceManager] = None


def get_device_manager() -> DeviceManager:
    global _GLOBAL_MANAGER
    if _GLOBAL_MANAGER is None:
        _GLOBAL_MANAGER = DeviceManager()
    return _GLOBAL_MANAGER


def get_primary_lamp() -> LampDevice:
    return get_device_manager().current
