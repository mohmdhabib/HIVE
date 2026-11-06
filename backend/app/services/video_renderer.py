import os
import shutil
import subprocess
import wave
import struct
import math
import json
import threading
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.schemas.video import (
    VideoProductionBlueprint,
    RenderJobStatus,
    SceneNode,
    SceneClipArtifact,
    SceneUpdateRequest,
)
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
        self.clips_dir = os.path.join(self.storage_dir, "clips")

        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.clips_dir, exist_ok=True)

        self.jobs: Dict[str, RenderJobStatus] = {}
        self.blueprints: Dict[str, VideoProductionBlueprint] = {}

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
            scene_clips=[],
        )
        self.jobs[job_id] = job
        self.jobs[blueprint.blueprint_id] = job
        self.blueprints[blueprint.blueprint_id] = blueprint
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

    def _calculate_natural_speech_duration(self, text: str) -> float:
        """Estimates natural human speaking tempo (~140 wpm, ~0.42s per word + 0.35s per clause break)."""
        if not text:
            return 3.2
        words = text.split()
        num_words = max(1, len(words))
        pause_count = text.count(",") + text.count(".") + text.count("!") + text.count("?") + text.count("—") + text.count(":") + text.count(";")
        raw_dur = (num_words * 0.42) + (pause_count * 0.35)
        return max(3.2, round(raw_dur, 2))

    def _get_audio_duration(self, file_path: str) -> float:
        """Measures exact duration in seconds of any audio file using wave header or FFmpeg inspection."""
        if not file_path or not os.path.exists(file_path):
            return 3.5

        # 1. Try pure wave header (instant 0ms)
        try:
            with wave.open(file_path, "r") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0 and frames > 0:
                    dur = frames / float(rate)
                    if dur > 0.1:
                        return round(dur, 2)
        except Exception:
            pass

        # 2. Inspect with FFmpeg (works on MP3, WAV, AAC, MP4, etc.)
        try:
            ffmpeg_bin = get_ffmpeg_binary()
            cmd = [ffmpeg_bin, "-i", file_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
            if match:
                h, m, s = match.groups()
                total = int(h) * 3600 + int(m) * 60 + float(s)
                if total > 0.1:
                    return round(total, 2)
        except Exception:
            pass

        return 3.5

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
        caption_position: str = "bottom",
        caption_font_size: Optional[int] = None,
        caption_highlight_color: Optional[str] = None,
        caption_style: str = "pill",
    ):
        """Renders viral short-form typography (Hormozi/TikTok style) with bottom lower-third positioning,
        bold outlines, high-contrast backdrop pills, and editable highlight colors."""
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

        # 2. Viral Short-Form Captions
        words = scene.audio.voiceover_text.split()
        if not words:
            words = ["HIVE", "AUTONOMOUS", "MEDIA"]

        # Break into punchy 2-4 word lines (max 20 chars per line), preserving all words without truncation
        lines = []
        curr = []
        for w in words:
            cand = " ".join(curr + [w])
            if len(cand) > 20 and len(curr) >= 2:
                lines.append(" ".join(curr).upper())
                curr = [w]
            else:
                curr.append(w)
        if curr:
            lines.append(" ".join(curr).upper())

        eff_font_size = caption_font_size if (caption_font_size and caption_font_size >= 24) else (72 if len(lines) <= 3 else 62)
        line_height = int(eff_font_size * 1.20)
        caption_font = self._get_font(eff_font_size)

        # Parse highlight color
        custom_h_rgb = (255, 230, 0)  # Default viral Gold/Yellow
        if caption_highlight_color and caption_highlight_color.startswith("#"):
            h = caption_highlight_color.lstrip("#")
            if len(h) == 3:
                h = "".join([c*2 for c in h])
            if len(h) == 6:
                try:
                    custom_h_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                except Exception:
                    pass

        # Identify highlight keywords
        emphasis_words = set(w.upper().strip(".,!?\"'") for w in scene.audio.voiceover_emphasis) if scene.audio.voiceover_emphasis else set()

        total_text_h = len(lines) * line_height
        pos = (caption_position or "bottom").lower()
        if "top" in pos:
            y_start = 320
        elif "center" in pos and "bottom" not in pos and "top" not in pos:
            y_start = (height - total_text_h) // 2
        else:
            # Default: standard viral lower-third (centered in bottom 1200-1550 safe zone)
            y_start = max(1000, min(1480 - total_text_h, 1420 - total_text_h))
        y = y_start

        for idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=caption_font, stroke_width=7)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) // 2

            # Check if any word in this line is an active highlight
            line_has_emphasis = any(w in emphasis_words for w in line.split()) or (scene_idx == 0 and idx == 0)
            highlight_color = (*custom_h_rgb, 255) if line_has_emphasis else (255, 255, 255, 255)

            # High-contrast backdrop pill for readability over any footage
            if caption_style == "pill":
                pill_pad_x = 24
                pill_pad_y = 6
                draw.rounded_rectangle(
                    [x - pill_pad_x, y - pill_pad_y, x + line_w + pill_pad_x, y + line_height - 10],
                    radius=18,
                    fill=(8, 10, 16, 180),
                )

            # Drop shadow
            draw.text((x + 3, y + 4), line, font=caption_font, fill=(0, 0, 0, 220))
            # Main bold text with thick black outline
            stroke_w = 7 if caption_style != "minimal" else 3
            draw.text((x, y), line, font=caption_font, fill=highlight_color, stroke_width=stroke_w, stroke_fill=(10, 10, 12, 255))
            y += line_height

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
        """Executes full end-to-end video assembly with real motion video footage, audio mixing, subtitles,
        and saves individual scene clips for preview and visual editing."""
        target_job_id = job_id or f"job-{blueprint.blueprint_id}"
        ffmpeg_bin = get_ffmpeg_binary()

        job = self.jobs.get(target_job_id)
        if not job:
            job = self.create_job(blueprint)

        # Permanent per-blueprint clip directory
        bp_clips_dir = os.path.join(self.clips_dir, blueprint.blueprint_id)
        os.makedirs(bp_clips_dir, exist_ok=True)
        try:
            with open(os.path.join(bp_clips_dir, "blueprint.json"), "w", encoding="utf-8") as f:
                f.write(blueprint.model_dump_json(indent=2))
        except Exception as e:
            logger.debug("Failed caching blueprint json: %s", e)

        try:
            logger.info("Initiating video render for blueprint '%s'", blueprint.blueprint_id)
            total_scenes = len(blueprint.scenes)
            scene_video_paths = []
            job.scene_clips = []

            # Step 1: For each scene, render real motion footage + voice cadence + ambient BGM + subtitle overlay
            for idx, scene in enumerate(blueprint.scenes):
                job.status = "generating_tts"
                job.progress_pct = 10.0 + (idx / total_scenes) * 70.0
                job.current_step = f"Compositing moving video footage for Scene {idx + 1}/{total_scenes}: {scene.emotional_beat.value.upper()}"

                scene_bg_video = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_motion.mp4")
                scene_overlay = os.path.join(bp_clips_dir, f"scene_{idx}_overlay.png")
                scene_voice = os.path.join(bp_clips_dir, f"scene_{idx}_voice.wav")
                scene_bgm = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_bgm.wav")
                scene_audio_mixed = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{idx}_mixed.wav")
                scene_mp4 = os.path.join(bp_clips_dir, f"scene_{idx}.mp4")
                scene_thumb = os.path.join(bp_clips_dir, f"scene_{idx}_thumb.jpg")

                # Step A: Synthesize Real AI Spoken Voiceover FIRST with natural speech timing
                natural_duration = self._calculate_natural_speech_duration(scene.audio.voiceover_text)
                voice_service.generate_voiceover(
                    text=scene.audio.voiceover_text,
                    worker_id=blueprint.worker_id,
                    duration_sec=natural_duration,
                    output_path=scene_voice,
                )

                # Step B: Measure EXACT voiceover duration and lock scene duration to prevent audio overlap
                voice_duration = self._get_audio_duration(scene_voice)
                duration = max(3.2, round(voice_duration + 0.50, 2))
                scene.duration_seconds = duration

                # Step C: Obtain real stock video, niche background loop, or kinetic motion footage matching exact duration
                material_service.get_scene_footage(
                    keywords=scene.visual.search_keywords,
                    worker_id=blueprint.worker_id,
                    scene_type=scene.emotional_beat.value,
                    duration_sec=duration,
                    output_path=scene_bg_video,
                    brand_color=blueprint.brand.colors.primary,
                    scene_idx=idx,
                    camera_motion=scene.visual.camera_motion,
                )

                # Step D: Render transparent subtitle and HUD overlay (default positioned at bottom lower-third)
                self._render_scene_overlay(
                    scene=scene,
                    blueprint=blueprint,
                    scene_idx=idx,
                    total_scenes=total_scenes,
                    output_path=scene_overlay,
                    caption_position="bottom",
                )

                # Step E: Ambient BGM + Audio Mixing with ZERO bleed and microsecond-level synchronization
                self._generate_ambient_bgm(duration_sec=duration, output_path=scene_bgm)
                fade_start = max(0.0, round(duration - 0.40, 2))
                sfx_path = sfx_service.get_sfx_path(scene.audio.sfx_cue)
                if sfx_path and os.path.exists(sfx_path):
                    mix_cmd = [
                        ffmpeg_bin, "-y",
                        "-i", scene_voice,
                        "-i", scene_bgm,
                        "-i", sfx_path,
                        "-filter_complex",
                        f"[0:a]apad=pad_dur=2.0,atrim=0:{duration}[v];"
                        f"[1:a]volume=0.18,atrim=0:{duration},afade=t=out:st={fade_start}:d=0.40[b];"
                        f"[2:a]volume=0.30,apad=pad_dur=2.0,atrim=0:{duration}[s];"
                        f"[v][b][s]amix=inputs=3:duration=first:dropout_transition=0,atrim=0:{duration}[a]",
                        "-map", "[a]",
                        "-c:a", "pcm_s16le",
                        scene_audio_mixed,
                    ]
                else:
                    mix_cmd = [
                        ffmpeg_bin, "-y",
                        "-i", scene_voice,
                        "-i", scene_bgm,
                        "-filter_complex",
                        f"[0:a]apad=pad_dur=2.0,atrim=0:{duration}[v];"
                        f"[1:a]volume=0.18,atrim=0:{duration},afade=t=out:st={fade_start}:d=0.40[b];"
                        f"[v][b]amix=inputs=2:duration=first:dropout_transition=0,atrim=0:{duration}[a]",
                        "-map", "[a]",
                        "-c:a", "pcm_s16le",
                        scene_audio_mixed,
                    ]
                subprocess.run(mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                # Step F: Composite moving video + subtitle overlay + mixed audio into final scene MP4
                job.status = "compositing"
                job.current_step = f"Burning animated subtitles & audio into Scene {idx + 1}/{total_scenes}"

                comp_cmd = [
                    ffmpeg_bin, "-y",
                    "-i", scene_bg_video,
                    "-i", scene_overlay,
                    "-i", scene_audio_mixed,
                    "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
                    "-map", "[v]",
                    "-map", "2:a",
                    "-t", str(duration),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    scene_mp4,
                ]
                subprocess.run(comp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                scene_video_paths.append(scene_mp4)

                # Extract individual scene thumbnail
                thumb_cmd = [
                    ffmpeg_bin, "-y",
                    "-ss", "00:00:00.6",
                    "-i", scene_mp4,
                    "-vframes", "1",
                    "-q:v", "2",
                    scene_thumb,
                ]
                subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Record individual scene clip artifact
                clip_artifact = SceneClipArtifact(
                    scene_idx=idx,
                    scene_id=scene.scene_id,
                    emotional_beat=scene.emotional_beat.value,
                    duration_seconds=round(duration, 1),
                    clip_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{idx}.mp4",
                    thumbnail_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{idx}_thumb.jpg" if os.path.exists(scene_thumb) else None,
                    overlay_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{idx}_overlay.png" if os.path.exists(scene_overlay) else None,
                    voice_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{idx}_voice.wav" if os.path.exists(scene_voice) else None,
                    voiceover_text=scene.audio.voiceover_text,
                    camera_motion=scene.visual.camera_motion,
                    search_keywords=scene.visual.search_keywords,
                    source_asset=scene.visual.description,
                    status="ready",
                )
                job.scene_clips.append(clip_artifact)

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
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-avoid_negative_ts", "make_zero",
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

            logger.info("Video successfully rendered! Output: %s (%.2f MB, %.1fs, %d scene clips)", final_mp4, size_mb, total_duration, len(job.scene_clips))

        except Exception as e:
            logger.exception("Video rendering failed for blueprint '%s'", blueprint.blueprint_id)
            job.status = "failed"
            job.current_step = f"Render failed: {e}"
            job.error_message = str(e)

        return job

    def render_single_scene(
        self,
        blueprint_id: str,
        scene_idx: int,
        update: SceneUpdateRequest,
    ) -> RenderJobStatus:
        """Regenerates a single scene clip with updated text, keywords, motion, or custom asset,
        and re-stitches the master video."""
        blueprint = self.blueprints.get(blueprint_id)
        bp_clips_dir = os.path.join(self.clips_dir, blueprint_id)

        if not blueprint and os.path.exists(os.path.join(bp_clips_dir, "blueprint.json")):
            try:
                with open(os.path.join(bp_clips_dir, "blueprint.json"), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    blueprint = VideoProductionBlueprint(**data)
                    self.blueprints[blueprint_id] = blueprint
            except Exception as e:
                logger.error("Failed loading cached blueprint: %s", e)

        if not blueprint:
            raise ValueError(f"Blueprint '{blueprint_id}' not found")

        if scene_idx < 0 or scene_idx >= len(blueprint.scenes):
            raise ValueError(f"Scene index {scene_idx} out of range (0-{len(blueprint.scenes)-1})")

        scene = blueprint.scenes[scene_idx]
        job = self.get_job(blueprint_id)
        if not job:
            job = self.create_job(blueprint)

        # Apply updates
        if update.voiceover_text is not None and update.voiceover_text.strip():
            scene.audio.voiceover_text = update.voiceover_text.strip()
        if update.search_keywords is not None and len(update.search_keywords) > 0:
            scene.visual.search_keywords = update.search_keywords
        if update.camera_motion is not None and update.camera_motion.strip():
            scene.visual.camera_motion = update.camera_motion.strip()
        if update.visual_description is not None and update.visual_description.strip():
            scene.visual.description = update.visual_description.strip()

        ffmpeg_bin = get_ffmpeg_binary()
        os.makedirs(bp_clips_dir, exist_ok=True)

        scene_bg_video = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{scene_idx}_motion.mp4")
        scene_overlay = os.path.join(bp_clips_dir, f"scene_{scene_idx}_overlay.png")
        scene_voice = os.path.join(bp_clips_dir, f"scene_{scene_idx}_voice.wav")
        scene_bgm = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{scene_idx}_bgm.wav")
        scene_audio_mixed = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_s{scene_idx}_mixed.wav")
        scene_mp4 = os.path.join(bp_clips_dir, f"scene_{scene_idx}.mp4")
        scene_thumb = os.path.join(bp_clips_dir, f"scene_{scene_idx}_thumb.jpg")

        # Step 1: Synthesize voiceover FIRST with natural speech timing
        natural_duration = self._calculate_natural_speech_duration(scene.audio.voiceover_text)
        voice_service.generate_voiceover(
            text=scene.audio.voiceover_text,
            worker_id=blueprint.worker_id,
            duration_sec=natural_duration,
            output_path=scene_voice,
        )

        # Step 2: Measure EXACT voiceover duration and lock scene duration to prevent audio cut-off
        voice_duration = self._get_audio_duration(scene_voice)
        duration = max(3.2, round(voice_duration + 0.50, 2))
        scene.duration_seconds = duration

        # Step 3: Visual background: if custom asset provided, use it directly
        if update.custom_asset_path and os.path.exists(update.custom_asset_path):
            if update.custom_asset_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                material_service.convert_image_to_motion_video(
                    update.custom_asset_path,
                    duration,
                    scene_bg_video,
                    motion_type=scene.visual.camera_motion,
                )
            else:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-stream_loop", "-1",
                    "-i", update.custom_asset_path,
                    "-t", str(duration),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-an",
                    scene_bg_video,
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:
            material_service.get_scene_footage(
                keywords=scene.visual.search_keywords,
                worker_id=blueprint.worker_id,
                scene_type=scene.emotional_beat.value,
                duration_sec=duration,
                output_path=scene_bg_video,
                brand_color=blueprint.brand.colors.primary,
                scene_idx=scene_idx,
                camera_motion=scene.visual.camera_motion,
            )

        # Step 4: Render transparent subtitle and HUD overlay with custom options
        self._render_scene_overlay(
            scene=scene,
            blueprint=blueprint,
            scene_idx=scene_idx,
            total_scenes=len(blueprint.scenes),
            output_path=scene_overlay,
            caption_position=update.caption_position or "bottom",
            caption_font_size=update.caption_font_size,
            caption_highlight_color=update.caption_highlight_color,
            caption_style=update.caption_style or "pill",
        )

        # Step 5: Ambient BGM & zero-bleed audio mixing
        self._generate_ambient_bgm(duration_sec=duration, output_path=scene_bgm)
        fade_start = max(0.0, round(duration - 0.40, 2))
        sfx_path = sfx_service.get_sfx_path(update.sfx_cue or scene.audio.sfx_cue)
        if sfx_path and os.path.exists(sfx_path):
            mix_cmd = [
                ffmpeg_bin, "-y",
                "-i", scene_voice,
                "-i", scene_bgm,
                "-i", sfx_path,
                "-filter_complex",
                f"[0:a]apad=pad_dur=2.0,atrim=0:{duration}[v];"
                f"[1:a]volume=0.18,atrim=0:{duration},afade=t=out:st={fade_start}:d=0.35[b];"
                f"[2:a]volume=0.30,apad=pad_dur=2.0,atrim=0:{duration}[s];"
                f"[v][b][s]amix=inputs=3:duration=first:dropout_transition=0,atrim=0:{duration}[a]",
                "-map", "[a]",
                "-c:a", "pcm_s16le",
                scene_audio_mixed,
            ]
        else:
            mix_cmd = [
                ffmpeg_bin, "-y",
                "-i", scene_voice,
                "-i", scene_bgm,
                "-filter_complex",
                f"[0:a]apad=pad_dur=2.0,atrim=0:{duration}[v];"
                f"[1:a]volume=0.18,atrim=0:{duration},afade=t=out:st={fade_start}:d=0.35[b];"
                f"[v][b]amix=inputs=2:duration=first:dropout_transition=0,atrim=0:{duration}[a]",
                "-map", "[a]",
                "-c:a", "pcm_s16le",
                scene_audio_mixed,
            ]
        subprocess.run(mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Step 6: Composite scene MP4
        comp_cmd = [
            ffmpeg_bin, "-y",
            "-i", scene_bg_video,
            "-i", scene_overlay,
            "-i", scene_audio_mixed,
            "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
            "-map", "[v]",
            "-map", "2:a",
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            scene_mp4,
        ]
        subprocess.run(comp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Extract thumb
        thumb_cmd = [
            ffmpeg_bin, "-y",
            "-ss", "00:00:00.6",
            "-i", scene_mp4,
            "-vframes", "1",
            "-q:v", "2",
            scene_thumb,
        ]
        subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Update artifact
        artifact = SceneClipArtifact(
            scene_idx=scene_idx,
            scene_id=scene.scene_id,
            emotional_beat=scene.emotional_beat.value,
            duration_seconds=round(duration, 1),
            clip_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{scene_idx}.mp4",
            thumbnail_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{scene_idx}_thumb.jpg" if os.path.exists(scene_thumb) else None,
            overlay_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{scene_idx}_overlay.png" if os.path.exists(scene_overlay) else None,
            voice_path=f"/storage/clips/{blueprint.blueprint_id}/scene_{scene_idx}_voice.wav" if os.path.exists(scene_voice) else None,
            voiceover_text=scene.audio.voiceover_text,
            camera_motion=scene.visual.camera_motion,
            search_keywords=scene.visual.search_keywords,
            source_asset=scene.visual.description,
            status="ready",
        )

        # Replace or append in job.scene_clips
        existing_idx = None
        for i, a in enumerate(job.scene_clips):
            if a.scene_idx == scene_idx:
                existing_idx = i
                break
        if existing_idx is not None:
            job.scene_clips[existing_idx] = artifact
        else:
            job.scene_clips.append(artifact)
            job.scene_clips.sort(key=lambda x: x.scene_idx)

        # Re-stitch master video from all scene_{i}.mp4 files
        all_scene_paths = []
        for i in range(len(blueprint.scenes)):
            spath = os.path.join(bp_clips_dir, f"scene_{i}.mp4")
            if os.path.exists(spath):
                all_scene_paths.append(spath)

        if len(all_scene_paths) == len(blueprint.scenes):
            concat_list = os.path.join(self.temp_dir, f"{blueprint.blueprint_id}_reconcat.txt")
            with open(concat_list, "w", encoding="utf-8") as f:
                for p in all_scene_paths:
                    safe_p = p.replace("\\", "/")
                    f.write(f"file '{safe_p}'\n")

            final_mp4 = os.path.join(self.video_dir, f"{blueprint.blueprint_id}.mp4")
            concat_cmd = [
                ffmpeg_bin, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-avoid_negative_ts", "make_zero",
                final_mp4,
            ]
            subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if os.path.exists(final_mp4):
                job.file_size_mb = round(os.stat(final_mp4).st_size / (1024 * 1024), 2)

        # Persist updated blueprint
        with open(os.path.join(bp_clips_dir, "blueprint.json"), "w", encoding="utf-8") as f:
            f.write(blueprint.model_dump_json(indent=2))

        job.status = "complete"
        job.progress_pct = 100.0
        job.current_step = f"Scene {scene_idx + 1} updated and master video re-stitched successfully!"
        return job

    def get_scene_clips(self, blueprint_id: str) -> List[SceneClipArtifact]:
        """Returns the list of scene clip artifacts for a blueprint."""
        job = self.get_job(blueprint_id)
        if job and job.scene_clips:
            return job.scene_clips

        # Inspect disk
        bp_clips_dir = os.path.join(self.clips_dir, blueprint_id)
        if not os.path.exists(bp_clips_dir):
            return []

        results = []
        blueprint = self.blueprints.get(blueprint_id)
        if not blueprint and os.path.exists(os.path.join(bp_clips_dir, "blueprint.json")):
            try:
                with open(os.path.join(bp_clips_dir, "blueprint.json"), "r", encoding="utf-8") as f:
                    blueprint = VideoProductionBlueprint(**json.load(f))
            except Exception:
                pass

        scenes = blueprint.scenes if blueprint else []
        for idx in range(len(scenes) if scenes else 12):
            clip_file = os.path.join(bp_clips_dir, f"scene_{idx}.mp4")
            if os.path.exists(clip_file):
                scene = scenes[idx] if idx < len(scenes) else None
                thumb_file = os.path.join(bp_clips_dir, f"scene_{idx}_thumb.jpg")
                overlay_file = os.path.join(bp_clips_dir, f"scene_{idx}_overlay.png")
                voice_file = os.path.join(bp_clips_dir, f"scene_{idx}_voice.wav")
                results.append(
                    SceneClipArtifact(
                        scene_idx=idx,
                        scene_id=scene.scene_id if scene else f"scene_{idx}",
                        emotional_beat=scene.emotional_beat.value if scene else "core",
                        duration_seconds=scene.duration_seconds if scene else 3.5,
                        clip_path=f"/storage/clips/{blueprint_id}/scene_{idx}.mp4",
                        thumbnail_path=f"/storage/clips/{blueprint_id}/scene_{idx}_thumb.jpg" if os.path.exists(thumb_file) else None,
                        overlay_path=f"/storage/clips/{blueprint_id}/scene_{idx}_overlay.png" if os.path.exists(overlay_file) else None,
                        voice_path=f"/storage/clips/{blueprint_id}/scene_{idx}_voice.wav" if os.path.exists(voice_file) else None,
                        voiceover_text=scene.audio.voiceover_text if scene else "",
                        camera_motion=scene.visual.camera_motion if scene else "ken_burns",
                        search_keywords=scene.visual.search_keywords if scene else [],
                        status="ready",
                    )
                )

        return results

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
