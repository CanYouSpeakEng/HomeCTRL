"""
sound_gen.py - Synthesizes custom tactile haptic sound effects for HomeCTRL.

Zero external dependencies: uses Python's built-in `wave`, `struct`, and `math`
to generate pristine, modern 44.1 kHz 16-bit PCM WAV files tailored for Apple HomeKit
tactile feedback.
"""

import os
import math
import wave
import struct

SAMPLE_RATE = 44100


def _write_wav(filename: str, samples: list):
    """Writes a list of normalized float samples (-1.0 to 1.0) into a 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)        # Mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(SAMPLE_RATE)
        raw_bytes = bytearray()
        for s in samples:
            # Clamp and convert to 16-bit signed int (-32767 to 32767)
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767)
            raw_bytes.extend(struct.pack("<h", int_val))
        wf.writeframes(raw_bytes)


def generate_popup_open(path: str):
    """Crisp, airy rising pop with soft resonance (HomeKit panel reveal)."""
    duration = 0.14  # 140ms
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 28.0) * math.sin(math.pi * min(1.0, t / 0.015))  # Smooth attack + rapid decay
        # Rising frequency sweep: 440 Hz -> 880 Hz
        freq = 520.0 + (360.0 * (t / duration))
        harmonic = 1040.0 + (720.0 * (t / duration))
        sample = (0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * harmonic * t)) * env
        samples.append(sample * 0.45)
    _write_wav(path, samples)


def generate_popup_close(path: str):
    """Subtle downward whisper dismissal (HomeKit panel hide)."""
    duration = 0.10  # 100ms
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 40.0)
        # Downward frequency sweep: 600 Hz -> 280 Hz
        freq = 600.0 - (320.0 * (t / duration))
        sample = math.sin(2 * math.pi * freq * t) * env
        samples.append(sample * 0.30)
    _write_wav(path, samples)


def generate_switch_on(path: str):
    """Tactile resonant high chime / contact click (Lamp ON)."""
    duration = 0.16  # 160ms
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 22.0)
        # Dual resonant frequencies (784 Hz G5 and 1174 Hz D6) with initial mechanical click
        click = math.exp(-t * 250.0) * (0.8 if i < int(SAMPLE_RATE * 0.003) else 0.0)
        tone = 0.65 * math.sin(2 * math.pi * 784.0 * t) + 0.35 * math.sin(2 * math.pi * 1174.0 * t)
        sample = (tone * env) + click
        samples.append(sample * 0.50)
    _write_wav(path, samples)


def generate_switch_off(path: str):
    """Soft warm damped mechanical click (Lamp OFF)."""
    duration = 0.12  # 120ms
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 35.0)
        # Deep warm frequencies (330 Hz E4 with rapid dampening)
        click = math.exp(-t * 200.0) * (0.6 if i < int(SAMPLE_RATE * 0.004) else 0.0)
        tone = math.sin(2 * math.pi * 330.0 * t)
        sample = (tone * env) + click
        samples.append(sample * 0.40)
    _write_wav(path, samples)


def generate_tick(path: str):
    """Sub-millisecond tactile haptic tick for sliders and swatches."""
    duration = 0.035  # 35ms
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 120.0)
        sample = math.sin(2 * math.pi * 1800.0 * t) * env
        samples.append(sample * 0.35)
    _write_wav(path, samples)


def generate_all_sounds(target_dir: str):
    """Generates all pristine haptic sound files."""
    os.makedirs(target_dir, exist_ok=True)
    sounds = {
        "open.wav": generate_popup_open,
        "close.wav": generate_popup_close,
        "switch_on.wav": generate_switch_on,
        "switch_off.wav": generate_switch_off,
        "tick.wav": generate_tick,
    }
    for fname, func in sounds.items():
        out_path = os.path.join(target_dir, fname)
        func(out_path)
        print(f"Generated tactile sound: {out_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    sounds_folder = os.path.join(base, "assets", "sounds")
    generate_all_sounds(sounds_folder)
