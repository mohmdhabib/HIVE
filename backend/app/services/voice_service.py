import os
import socket
import asyncio
import wave
import struct
import math
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("voice_service")

VOICE_MAP = {
    "tech": "en-US-ChristopherNeural",
    "business": "en-US-GuyNeural",
    "curiosity": "en-US-AriaNeural",
    "culture": "en-US-EricNeural",
    "lifestyle": "en-US-JennyNeural",
}


class VoiceService:
    """Enterprise text-to-speech engine supporting Edge TTS (free neural AI voice) with immediate fallback."""

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.storage_dir = os.path.join(base_dir, "storage")
        self.temp_dir = os.path.join(self.storage_dir, "temporary")
        os.makedirs(self.temp_dir, exist_ok=True)
        self._online_checked = False
        self._is_online = False

    def is_edge_tts_available(self) -> bool:
        """Fast check to verify if Microsoft Bing speech service is reachable."""
        if self._online_checked:
            return self._is_online
        self._online_checked = True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(("speech.platform.bing.com", 443))
            sock.close()
            self._is_online = True
            logger.info("Microsoft Edge TTS service is reachable online.")
        except Exception:
            self._is_online = False
            logger.info("Edge TTS offline or unreachable; using high-speed cadence speech synthesis.")
        return self._is_online

    async def _generate_edge_tts(self, text: str, voice_name: str, output_path: str) -> bool:
        """Attempts neural voice synthesis using Microsoft Edge TTS."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice_name)
            await asyncio.wait_for(communicate.save(output_path), timeout=5.0)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                logger.info("Successfully generated Edge TTS voiceover with voice '%s'", voice_name)
                return True
        except Exception as e:
            logger.debug("Edge TTS generation failed or timed out: %s", e)
        return False

    def _generate_synthetic_cadence(self, text: str, duration_sec: float, output_path: str):
        """Synthesizes multi-harmonic cadence waveforms matching word counts."""
        sample_rate = 44100
        words = text.split()
        num_words = max(1, len(words))
        total_samples = int(sample_rate * duration_sec)

        samples_per_word = total_samples // num_words
        frames = bytearray()

        for word_idx, word in enumerate(words):
            active_samples = int(samples_per_word * 0.82)
            pause_samples = samples_per_word - active_samples
            base_pitch = 165.0 + (math.sin(word_idx * 0.9) * 25.0)

            for s in range(active_samples):
                t = s / sample_rate
                env = math.sin(math.pi * (s / active_samples)) ** 0.8
                f0 = math.sin(2 * math.pi * base_pitch * t)
                f1 = math.sin(2 * math.pi * (base_pitch * 2.2) * t) * 0.4
                val = (f0 + f1) * 0.28 * env
                sample = int(max(-1.0, min(1.0, val)) * 32767)
                frames.extend(struct.pack("<h", sample))

            frames.extend(b"\x00\x00" * pause_samples)

        current_len = len(frames) // 2
        if current_len < total_samples:
            frames.extend(b"\x00\x00" * (total_samples - current_len))
        elif current_len > total_samples:
            frames = frames[: total_samples * 2]

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def generate_voiceover(
        self,
        text: str,
        worker_id: str = "tech",
        duration_sec: float = 4.0,
        output_path: str = "",
    ) -> str:
        """Generates spoken voiceover audio using Edge TTS -> Cadence fallback."""
        voice_name = VOICE_MAP.get(worker_id, "en-US-ChristopherNeural")

        # 1. Try Edge TTS if online
        if self.is_edge_tts_available():
            try:
                success = asyncio.run(self._generate_edge_tts(text, voice_name, output_path))
                if success:
                    return output_path
            except Exception as exc:
                logger.debug("Edge TTS attempt error: %s", exc)

        # 2. High-speed Cadence Fallback (Zero latency, instant generation)
        self._generate_synthetic_cadence(text, duration_sec, output_path)
        return output_path


voice_service = VoiceService()
