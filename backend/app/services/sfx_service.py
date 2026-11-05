import os
import wave
import struct
import math
from typing import Dict, Optional
from app.core.logging import get_logger

logger = get_logger("sfx_service")


class SFXService:
    """Provides synthesized studio sound effects for scene transitions and emotional beats."""

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.storage_dir = os.path.join(base_dir, "storage")
        self.sfx_dir = os.path.join(self.storage_dir, "sfx")
        os.makedirs(self.sfx_dir, exist_ok=True)
        self._ensure_default_sfx()

    def _ensure_default_sfx(self):
        """Generates studio-grade WAV sound effects if they don't already exist."""
        sfx_files = {
            "whoosh": self._generate_whoosh,
            "pop": self._generate_pop,
            "impact": self._generate_impact,
            "chime": self._generate_chime,
        }
        for name, gen_fn in sfx_files.items():
            fpath = os.path.join(self.sfx_dir, f"{name}.wav")
            if not os.path.exists(fpath):
                gen_fn(fpath)

    def _generate_whoosh(self, output_path: str):
        """Generates a cinematic transition swoosh (0.4s)."""
        sample_rate = 44100
        duration = 0.45
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / duration)) ** 1.5
            freq = 220 + (math.sin(math.pi * (t / duration)) * 800)
            val = math.sin(2 * math.pi * freq * t) * 0.45 * env
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_pop(self, output_path: str):
        """Generates a snappy UI pop sound (0.12s)."""
        sample_rate = 44100
        duration = 0.12
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 35.0)
            freq = 950 - (t * 4000)
            val = math.sin(2 * math.pi * max(100, freq) * t) * 0.6 * env
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_impact(self, output_path: str):
        """Generates a deep sub-bass cinematic impact boom (0.7s)."""
        sample_rate = 44100
        duration = 0.7
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 5.0)
            freq = 65 - (t * 25)
            val = math.sin(2 * math.pi * max(35, freq) * t) * 0.75 * env
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_chime(self, output_path: str):
        """Generates a bright notification chime bell (0.5s)."""
        sample_rate = 44100
        duration = 0.55
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 7.0)
            c1 = math.sin(2 * math.pi * 1318.5 * t) * 0.25 # E6
            c2 = math.sin(2 * math.pi * 1661.2 * t) * 0.20 # G#6
            c3 = math.sin(2 * math.pi * 2093.0 * t) * 0.15 # C7
            val = (c1 + c2 + c3) * env
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def get_sfx_path(self, cue_name: Optional[str]) -> Optional[str]:
        if not cue_name:
            return None
        clean = cue_name.lower().replace("_", "").replace("-", "")
        if "whoosh" in clean or "swoosh" in clean or "transition" in clean:
            return os.path.join(self.sfx_dir, "whoosh.wav")
        if "pop" in clean or "click" in clean or "tap" in clean:
            return os.path.join(self.sfx_dir, "pop.wav")
        if "impact" in clean or "boom" in clean or "bass" in clean or "thud" in clean:
            return os.path.join(self.sfx_dir, "impact.wav")
        if "chime" in clean or "bell" in clean or "ding" in clean or "reveal" in clean:
            return os.path.join(self.sfx_dir, "chime.wav")
        return os.path.join(self.sfx_dir, "whoosh.wav")


sfx_service = SFXService()
