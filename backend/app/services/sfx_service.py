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
            "riser": self._generate_riser,
            "glitch": self._generate_glitch,
            "cash_register": self._generate_cash_register,
            "camera_click": self._generate_camera_click,
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

    def _generate_riser(self, output_path: str):
        """Generates a cinematic tension riser sweeping up from 120Hz to 950Hz (1.0s)."""
        sample_rate = 44100
        duration = 1.0
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = (t / duration) ** 1.6
            freq = 120 + ((t / duration) ** 2.0) * 830
            mod = 1.0 + (math.sin(2 * math.pi * 12.0 * t) * 0.2)
            val = math.sin(2 * math.pi * freq * t) * 0.65 * env * mod
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_glitch(self, output_path: str):
        """Generates a cyber digital glitch burst (0.28s)."""
        sample_rate = 44100
        duration = 0.28
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env = 1.0 - (t / duration)
            step = int(t * 180) % 5
            freq = [1800, 420, 2600, 140, 3100][step]
            val = (1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0) * 0.35 * env
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_cash_register(self, output_path: str):
        """Generates a rewarding cha-ching payment / revenue cue (0.45s)."""
        sample_rate = 44100
        duration = 0.45
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env1 = math.exp(-t * 8.0)
            env2 = math.exp(-max(0.0, t - 0.12) * 12.0) if t >= 0.12 else 0.0
            bell = math.sin(2 * math.pi * 2093.0 * t) * 0.45 * env1
            shimmer = math.sin(2 * math.pi * 3136.0 * t) * 0.35 * env2
            val = bell + shimmer
            sample = int(max(-1.0, min(1.0, val)) * 32767)
            frames.extend(struct.pack("<h", sample))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _generate_camera_click(self, output_path: str):
        """Generates a crisp mechanical shutter snap (0.2s)."""
        sample_rate = 44100
        duration = 0.20
        total_samples = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            env1 = math.exp(-t * 60.0)
            env2 = math.exp(-max(0.0, t - 0.08) * 50.0) if t >= 0.08 else 0.0
            click1 = math.sin(2 * math.pi * 1400.0 * t) * 0.6 * env1
            click2 = math.sin(2 * math.pi * 900.0 * t) * 0.5 * env2
            val = click1 + click2
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
        if "impact" in clean or "boom" in clean or "bass" in clean or "thud" in clean:
            return os.path.join(self.sfx_dir, "impact.wav")
        if "chime" in clean or "bell" in clean or "ding" in clean or "reveal" in clean:
            return os.path.join(self.sfx_dir, "chime.wav")
        if "riser" in clean or "tension" in clean or "build" in clean or "suspense" in clean:
            return os.path.join(self.sfx_dir, "riser.wav")
        if "glitch" in clean or "cyber" in clean or "digital" in clean:
            return os.path.join(self.sfx_dir, "glitch.wav")
        if "cash" in clean or "money" in clean or "chaching" in clean or "revenue" in clean:
            return os.path.join(self.sfx_dir, "cash_register.wav")
        if "camera" in clean or "photo" in clean or "snap" in clean or "shutter" in clean:
            return os.path.join(self.sfx_dir, "camera_click.wav")
        if "pop" in clean or "click" in clean or "tap" in clean:
            return os.path.join(self.sfx_dir, "pop.wav")
        return os.path.join(self.sfx_dir, "whoosh.wav")

    def list_available_sfx(self) -> list[dict]:
        return [
            {"id": "whoosh", "name": "Cinematic Whoosh", "category": "Transition", "preview": "whoosh"},
            {"id": "impact", "name": "Sub-Bass Impact", "category": "Hook & Hit", "preview": "impact"},
            {"id": "pop", "name": "Snappy UI Pop", "category": "UI & Accent", "preview": "pop"},
            {"id": "chime", "name": "Bell Chime", "category": "Reveal & Insight", "preview": "chime"},
            {"id": "riser", "name": "Tension Riser", "category": "Build & Suspense", "preview": "riser"},
            {"id": "glitch", "name": "Digital Cyber Glitch", "category": "Cut & Transition", "preview": "glitch"},
            {"id": "cash_register", "name": "Cha-Ching Cash Register", "category": "Payoff & Revenue", "preview": "cash_register"},
            {"id": "camera_click", "name": "Shutter Snap", "category": "Visual Reveal", "preview": "camera_click"},
        ]


sfx_service = SFXService()
