"""
sound.py - Tactile Haptic Audio Player for HomeCTRL.

Plays ultra-low latency, custom-synthesized WAV feedback on Windows
using built-in winsound. Zero external audio libraries required.
"""

import os
import sys
import threading
try:
    import winsound
except ImportError:
    winsound = None


def _get_sound_dir() -> str:
    """Locates assets/sounds directory across dev mode and frozen PyInstaller."""
    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "assets", "sounds"))
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "assets", "sounds"))
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        candidates.append(os.path.join(localapp, "HomeCTRL", "assets", "sounds"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds"))
    candidates.append(os.path.join(os.getcwd(), "assets", "sounds"))

    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0] if candidates else ""


class SoundFX:
    """Manages playback of tactile feedback sound effects."""

    _SOUND_DIR = _get_sound_dir()
    _ENABLED = True

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._ENABLED = enabled

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._ENABLED

    @classmethod
    def _play(cls, filename: str):
        if not cls._ENABLED or not winsound:
            return
        filepath = os.path.join(cls._SOUND_DIR, filename)
        if not os.path.exists(filepath):
            return

        def _worker():
            try:
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            except Exception:
                pass

        # Run in lightweight daemon thread to guarantee non-blocking UI
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    @classmethod
    def play_open(cls):
        cls._play("open.wav")

    @classmethod
    def play_close(cls):
        cls._play("close.wav")

    @classmethod
    def play_switch_on(cls):
        cls._play("switch_on.wav")

    @classmethod
    def play_switch_off(cls):
        cls._play("switch_off.wav")

    @classmethod
    def play_tick(cls):
        cls._play("tick.wav")
