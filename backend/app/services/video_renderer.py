import os
import shutil
import subprocess
import wave
import struct
import math
import threading
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.schemas.video import VideoProductionBlueprint, RenderJobStatus, SceneNode
from app.workers.registry import get_worker
from app.services.material_service import material_service
from app.services.voice_service import voice_service
from app.services.sfx_service import sfx_service
from app.core.logging import get_logger

logger = get_logger("video_renderer")

# Locate FFmpeg binary
def get_ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe):
            return exe
    except Exception:
        pass
    which = shutil.which("ffmpeg")
    return which if which else "ffmpeg"


class VideoRenderService:
    def __init__(self):
        # Resolve storage paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.storage_dir = os.path.join(base_dir, "storage")
        if not os.path.exists(self.storage_dir):
            if os.path.exists("/app/storage"):
                self.storage_dir = "/app/storage"
            elif os.path.exists(os.path.join(base_dir, "..", "storage")):
                self.storage_dir = os.path.abspath(os.path.join(base_dir, "..", "storage"))
        self.video_dir = os.path.join(self.storage_dir, "videos")
        self.image_dir = os.path.join(self.storage_dir, "images")
        self.temp_dir = os.path.join(self.storage_dir, "temporary")

        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self.jobs: Dict[str, RenderJobStatus] = {}

    def get_job(self, job_or_blueprint_id: str) -> Optional[RenderJobStatus]:
        if job_or_blueprint_id in self.jobs:
            return self.jobs[job_or_blueprint_id]
        for j in self.jobs.values():
            if j.blueprint_id == job_or_blueprint_id:
                return j
        return None

    def create_job(self, blueprint: VideoProductionBlueprint) -> RenderJobStatus:
        job_id = f"job-{blueprint.blueprint_id}"
        job = RenderJobStatus(
            job_id=job_id,
            blueprint_id=blueprint.blueprint_id,
            worker_id=blueprint.worker_id,
            status="queued",
            progress_pct=5.0,
            current_step="Queued for automated video composition",
        )
        self.jobs[job_id] = job
        self.jobs[blueprint.blueprint_id] = job
        return job

    def list_rendered_videos(self) -> List[Dict]:
        items = []
        if os.path.exists(self.video_dir):
            for fname in sorted(os.listdir(self.video_dir), reverse=True):
                if fname.endswith(".mp4"):
                    fpath = os.path.join(self.video_dir, fname)
                    stat = os.stat(fpath)
                    b_id = fname.replace(".mp4", "")
                    thumb_url = f"/storage/images/{b_id}_thumb.jpg"
                    if not os.path.exists(os.path.join(self.image_dir, f"{b_id}_thumb.jpg")):
                        thumb_url = None
                    items.append({
                        "blueprint_id": b_id,
                        "filename": fname,
                        "video_url": f"/storage/videos/{fname}",
                        "thumbnail_url": thumb_url,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    })
        return items

    def _generate_speech_cadence(self, text: str, duration_sec: float, output_path: str):
        """Generates dynamic, multi-frequency rhythmic speech cadence waveforms with word-level inflection."""
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
            if word_idx == 0:
                base_pitch += 20.0

            for s in range(active_samples):
                t = s / sample_rate
                env = math.sin(math.pi * (s / active_samples)) ** 0.8
                f0 = math.sin(2 * math.pi * base_pitch * t)
                f1 = math.sin(2 * math.pi * (base_pitch * 2.2) * t) * 0.4
                f2 = math.sin(2 * math.pi * (base_pitch * 4.1) * t) * 0.2
                val = (f0 + f1 + f2) * 0.28 * env
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

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Loads a bold viral sans-serif font for captions (Impact, Arial Bold, Segoe UI Bold)."""
        font_candidates = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for fp in font_candidates:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _generate_ambient_bgm(self, duration_sec: float, output_path: str):
        """Uses studio lo-fi beat track from storage/bgm/ or synthesizes rhythmic background music."""
        bgm_dir = os.path.join(self.storage_dir, "bgm")
        curated_beat = os.path.join(bgm_dir, "cyber_beat.wav")
        ffmpeg_bin = get_ffmpeg_binary()

        if os.path.exists(curated_beat) and os.path.getsize(curated_beat) > 50000:
            try:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-stream_loop", "-1",
                    "-i", curated_beat,
                    "-t", str(duration_sec),
                    "-c:a", "pcm_s16le",
                    output_path,
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    return
            except Exception as e:
                logger.debug("Failed cutting curated BGM: %s", e)

        # Fallback harmonic synthwave
        sample_rate = 44100
        total_samples = int(sample_rate * duration_sec)
        frames = bytearray()
        chords = [
            (55.0, 220.0, 261.63, 329.63),
            (43.65, 174.61, 220.0, 261.63),
            (65.41, 196.0, 261.63, 329.63),
            (49.0, 196.0, 246.94, 293.66),
        ]
        for i in range(total_samples):
            t = i / sample_rate
            chord_idx = int((t / 2.5) % len(chords))
            root, p1, p2, p3 = chords[chord_idx]
            bass = math.sin(2 * math.pi * root * t) * 0.30
            pad1 = math.sin(2 * math.pi * p1 * t) * 0.10
            pad2 = math.sin(2 * math.pi * p2 * t) * 0.08
            pad3 = math.sin(2 * math.pi * p3 * t) * 0.06
            beat_phase = t % 0.5
            tick = math.sin(2 * math.pi * 3500 * t) * math.exp(-beat_phase * 40) * 0.06
            val = max(-1.0, min(1.0, (bass + pad1 + pad2 + pad3 + tick) * 0.8))
            frames.extend(struct.pack("<h", int(val * 32767)))

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(frames)

    def _render_scene_overlay(
        self,
        scene: SceneNode,
        blueprint: VideoProductionBlueprint,
        scene_idx: int,
        total_scenes: int,
        output_path: str,
    ):
        """Renders viral short-form typography (Hormozi/TikTok style) with bold outlines and keyword highlighting."""
        width, height = 1080, 1920
        img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        primary_hex = blueprint.brand.colors.primary.lstrip("#")
        p_rgb = tuple(int(primary_hex[i:i+2], 16) for i in (0, 2, 4)) if len(primary_hex) == 6 else (0, 212, 255)

        # 1. Sleek, minimal channel badge pill (top-left)
        badge_font = self._get_font(26)
        brand_label = blueprint.brand.brand_name.upper()
        draw.rounded_rectangle([60, 80, 360, 136], radius=28, fill=(10, 14, 22, 175), outline=(255, 255, 255, 45), width=1)
        draw.ellipse([82, 102, 94, 114], fill=(*p_rgb, 255))
        draw.text((106, 95), brand_label[:18], font=badge_font, fill=(255, 255, 255, 235))

        # 2. Viral Short-Form Captions (Centered Lower-Third, Impact/Arial Bold, thick outline, word highlights)
        caption_font = self._get_font(74)
        words = scene.audio.voiceover_text.split()
        if not words:
            words = ["HIVE", "AUTONOMOUS", "MEDIA"]

        # Break into 2 punchy lines maximum (3-5 words each)
        half = max(1, len(words) // 2)
        if len(words) > 5:
            line_a = " ".join(words[:half]).upper()
            line_b = " ".join(words[half:half*2]).upper()
            lines = [line_a, line_b]
        else:
            lines = [" ".join(words).upper()]

        # Identify highlight keywords
        emphasis_words = set(w.upper().strip(".,!?\"'") for w in scene.audio.voiceover_emphasis) if scene.audio.voiceover_emphasis else set()

        y_start = 1320 if len(lines) == 2 else 1360
        y = y_start

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=caption_font, stroke_width=6)
            w = bbox[2] - bbox[0]
            x = (width - w) // 2

            # Check if any word in this line is an active highlight
            line_has_emphasis = any(w in emphasis_words for w in line.split()) or (scene_idx == 0 and ("STOP" in line or "AI" in line or "2023" in line))
            highlight_color = (255, 235, 59, 255) if line_has_emphasis else (255, 255, 255, 255)

            # Drop shadow
            draw.text((x + 4, y + 5), line, font=caption_font, fill=(0, 0, 0, 190))
            # Main bold text with thick black outline
            draw.text((x, y), line, font=caption_font, fill=highlight_color, stroke_width=7, stroke_fill=(12, 12, 14, 255))
            y += 92

        img.save(output_path, "PNG")

    def _render_scene_image(
        self,
        scene: SceneNode,
        blueprint: VideoProductionBlueprint,
        scene_idx: int,
        total_scenes: int,
        output_path: str,
    ):
        """Renders an eye-catching YouTube Shorts / TikTok thumbnail cover."""
        width, height = 1080, 1920
        img = Image.new("RGB", (width, height), color=(12, 16, 26))
        draw = ImageDraw.Draw(img)

        primary_hex = blueprint.brand.colors.primary.lstrip("#")
        p_rgb = tuple(int(primary_hex[i:i+2], 16) for i in (0, 2, 4)) if len(primary_hex) == 6 else (0, 212, 255)

        # Background glowing vignette
        for r in range(400, 0, -20):
            alpha = int(35 * (1.0 - r / 400.0))
            draw.ellipse([540 - r, 800 - r, 540 + r, 800 + r], outline=(*p_rgb,), width=3)

        # Brand pill top
        badge_font = self._get_font(32)
        draw.rounded_rectangle([100, 140, 480, 210], radius=35, fill=(20, 26, 40), outline=(*p_rgb,), width=2)
        draw.ellipse([130, 165, 150, 185], fill=(*p_rgb,))
        draw.text((170, 158), blueprint.brand.brand_name.upper(), font=badge_font, fill=(255, 255, 255))

        # Huge Thumbnail Hook Title
        title_font = self._get_font(84)
        words = blueprint.title.upper().split()
        title_lines = []
        curr = []
        for w in words:
            curr.append(w)
            if len(" ".join(curr)) > 15:
                title_lines.append(" ".join(curr))
                curr = []
        if curr:
            title_lines.append(" ".join(curr))

        ty = 780
        for idx, tline in enumerate(title_lines[:4]):
            t_bbox = draw.textbbox((0, 0), tline, font=title_font, stroke_width=8)
            tw = t_bbox[2] - t_bbox[0]
            tx = (width - tw) // 2
            tcolor = (255, 235, 59) if idx % 2 == 1 else (255, 255, 255)
            draw.text((tx, ty), tline, font=title_font, fill=tcolor, stroke_width=8, stroke_fill=(5, 5, 5))
            ty += 105

        img.save(output_path, "JPEG", quality=92)

    def render_blueprint(
        self,
        blueprint: VideoProductionBlueprint,
        job_id: Optional[str] = None,
    ) -> RenderJobStatus:
        """Executes full end-to-end video assembly with real motion video footage, audio mixing, and subtitles."""
        target_job_id = job_id or f"job-{blueprint.blueprint_id}"
        ffmpeg_bin = get_ffmpeg_binary()

        job = self.jobs.get(target_job_id)
        if not job:
            job = self.create_job(blueprint)

        try:
            logger.info("Initiating video render for blueprint '%s'", blueprint.blueprint_id)
            total_scenes = len(blueprint.scenes)
            scene_video_paths = []

            # Step 1: For each scene, render real motion footage + voice cadence + ambient BGM + subtitle overlay
            for idx, scene in enumerate(blueprint.scenes):
                job.status = "generating_tts"
                job.progress_pct = 10.0 + (idx / total_scenes) * 35.0
                job.current_step = f"Compositing moving video footage for Scene {idx + 1}/{total_scenes}: {scene.emotional_beat.value.upper()}"

                duration = max(3.0, scene.duration_seconds)
                scene_bg_video = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_motion.mp4")
                scene_overlay = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_overlay.png")
                scene_voice = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_voice.wav")
                scene_bgm = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_bgm.wav")
                scene_audio_mixed = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_mixed.wav")
                scene_mp4 = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}.mp4")

                # Step A: Obtain real stock video, niche background loop, or kinetic motion footage
                material_service.get_scene_footage(
                    keywords=scene.visual.search_keywords,
                    worker_id=blueprint.worker_id,
                    scene_type=scene.emotional_beat.value,
                    duration_sec=duration,
                    output_path=scene_bg_video,
                    brand_color=blueprint.brand.colors.primary,
                )

                # Step B: Render transparent subtitle and HUD overlay
                self._render_scene_overlay(
                    scene=scene,
                    blueprint=blueprint,
                    scene_idx=idx,
                    total_scenes=total_scenes,
                    output_path=scene_overlay,
                )

                # Step C: Synthesize Real AI Spoken Voiceover & Lo-Fi Ambiance & SFX
                voice_service.generate_voiceover(
                    text=scene.audio.voiceover_text,
                    worker_id=blueprint.worker_id,
                    duration_sec=duration,
                    output_path=scene_voice,
                )
                self._generate_ambient_bgm(duration_sec=duration, output_path=scene_bgm)

                sfx_path = sfx_service.get_sfx_path(scene.audio.sfx_cue)
                if sfx_path and os.path.exists(sfx_path):
                    mix_cmd = [
                        ffmpeg_bin, "-y",
                        "-i", scene_voice,
                        "-i", scene_bgm,
                        "-i", sfx_path,
                        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.18[b];[2:a]volume=0.35[s];[v][b][s]amix=inputs=3:duration=first:dropout_transition=2[a]",
                        "-map", "[a]",
                        "-c:a", "pcm_s16le",
                        scene_audio_mixed,
                    ]
                else:
                    mix_cmd = [
                        ffmpeg_bin, "-y",
                        "-i", scene_voice,
                        "-i", scene_bgm,
                        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.18[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2[a]",
                        "-map", "[a]",
                        "-c:a", "pcm_s16le",
                        scene_audio_mixed,
                    ]
                subprocess.run(mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                # Step D: Composite moving video + subtitle overlay + mixed audio into final scene MP4
                job.status = "compositing"
                job.progress_pct = 45.0 + (idx / total_scenes) * 35.0
                job.current_step = f"Burning animated subtitles & audio into Scene {idx + 1}/{total_scenes}"

                comp_cmd = [
                    ffmpeg_bin, "-y",
                    "-i", scene_bg_video,
                    "-i", scene_overlay,
                    "-i", scene_audio_mixed,
                    "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
                    "-map", "[v]",
                    "-map", "2:a",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    scene_mp4,
                ]
                subprocess.run(comp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                scene_video_paths.append(scene_mp4)

            # Step 2: Concatenate Scene Clips into Final MP4
            job.status = "encoding"
            job.progress_pct = 85.0
            job.current_step = "Concatenating scene clips and assembling final H.264 MP4 container..."

            concat_list_file = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_concat.txt")
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for p in scene_video_paths:
                    safe_p = p.replace("\\", "/")
                    f.write(f"file '{safe_p}'\n")

            final_mp4 = os.path.join(self.video_dir, f"{blueprint.blueprint_id}.mp4")
            concat_cmd = [
                ffmpeg_bin, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_file,
                "-c", "copy",
                final_mp4,
            ]
            subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Step 3: Extract True Video Thumbnail via FFmpeg
            job.current_step = "Generating high-definition video thumbnail..."
            thumb_path = os.path.join(self.image_dir, f"{blueprint.blueprint_id}_thumb.jpg")
            if os.path.exists(final_mp4):
                thumb_cmd = [
                    ffmpeg_bin, "-y",
                    "-ss", "00:00:01.5",
                    "-i", final_mp4,
                    "-vframes", "1",
                    "-q:v", "2",
                    thumb_path,
                ]
                subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Step 4: Finalize Job Status
            file_stat = os.stat(final_mp4)
            size_mb = round(file_stat.st_size / (1024 * 1024), 2)
            total_duration = sum(s.duration_seconds for s in blueprint.scenes)

            job.status = "complete"
            job.progress_pct = 100.0
            job.current_step = "Render complete! Real 1080x1920 motion video ready for review & distribution."
            job.output_path = f"/storage/videos/{blueprint.blueprint_id}.mp4"
            job.thumbnail_path = f"/storage/images/{blueprint.blueprint_id}_thumb.jpg"
            job.duration_seconds = round(total_duration, 1)
            job.file_size_mb = size_mb

            logger.info("Video successfully rendered! Output: %s (%.2f MB, %.1fs)", final_mp4, size_mb, total_duration)

        except Exception as e:
            logger.exception("Video rendering failed for blueprint '%s'", blueprint.blueprint_id)
            job.status = "failed"
            job.current_step = f"Render failed: {e}"
            job.error_message = str(e)

        return job

    def start_background_render(self, blueprint: VideoProductionBlueprint) -> RenderJobStatus:
        """Starts asynchronous background render and returns initial job object immediately."""
        job = self.create_job(blueprint)
        thread = threading.Thread(
            target=self.render_blueprint,
            args=(blueprint, job.job_id),
            daemon=True,
        )
        thread.start()
        return job


video_renderer = VideoRenderService()
