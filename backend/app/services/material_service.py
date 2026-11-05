import os
import math
import subprocess
import json
import urllib.request
from typing import List, Optional
from PIL import Image, ImageDraw

from app.core.logging import get_logger

logger = get_logger("material_service")


def get_ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"


class MaterialService:
    """Manages real stock video footage (Pexels / Pixabay) and procedural 30 FPS kinetic motion footage."""

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.storage_dir = os.path.join(base_dir, "storage")
        if not os.path.exists(self.storage_dir):
            if os.path.exists("/app/storage"):
                self.storage_dir = "/app/storage"
            elif os.path.exists(os.path.join(base_dir, "..", "storage")):
                self.storage_dir = os.path.abspath(os.path.join(base_dir, "..", "storage"))

        self.materials_dir = os.path.join(self.storage_dir, "materials")
        self.downloads_dir = os.path.join(self.materials_dir, "downloads")
        self.temp_dir = os.path.join(self.storage_dir, "temporary")

        os.makedirs(self.materials_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def fetch_pexels_stock_video(
        self,
        keywords: List[str],
        api_key: Optional[str] = None,
        duration_needed: float = 4.0,
    ) -> Optional[str]:
        """Queries Pexels for real 9:16 portrait stock video clips matching the keywords."""
        key = api_key or os.getenv("PEXELS_API_KEY", "").strip()
        if not key or not keywords:
            return None

        query = "+".join(keywords[:3])
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"

        try:
            req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "HIVE-VideoEngine/2.0"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                videos = data.get("videos", [])
                if not videos:
                    return None

                # Find best HD portrait video file
                first_video = videos[0]
                video_files = first_video.get("video_files", [])
                # Prefer 1080x1920 or 720x1280
                target_file = None
                for vf in video_files:
                    if vf.get("width", 0) <= vf.get("height", 0):  # Vertical
                        target_file = vf.get("link")
                        break
                if not target_file and video_files:
                    target_file = video_files[0].get("link")

                if target_file:
                    safe_fname = f"pexels_{query}_{first_video['id']}.mp4"
                    dest_path = os.path.join(self.downloads_dir, safe_fname)
                    if not os.path.exists(dest_path):
                        logger.info("Downloading real stock video from Pexels: %s", target_file)
                        urllib.request.urlretrieve(target_file, dest_path)
                    return dest_path

        except Exception as e:
            logger.debug("Pexels fetch skipped or unavailable: %s", e)

        return None

    def get_scene_footage(
        self,
        keywords: List[str],
        worker_id: str,
        scene_type: str,
        duration_sec: float,
        output_path: str,
        brand_color: str = "#00d4ff",
    ) -> str:
        """Retrieves real stock video, niche background loop, or renders procedural kinetic footage."""
        ffmpeg_bin = get_ffmpeg_binary()

        # 1. Attempt Pexels Stock Video API
        stock_path = self.fetch_pexels_stock_video(keywords=keywords, duration_needed=duration_sec)
        if stock_path and os.path.exists(stock_path):
            try:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-stream_loop", "-1",
                    "-i", stock_path,
                    "-t", str(duration_sec),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-an",
                    output_path,
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    return output_path
            except Exception as e:
                logger.debug("Failed trimming stock footage: %s", e)

        # 2. Check for local niche video footage in storage/materials/
        niche_names = [f"{worker_id}_loop.mp4", "tech_loop.mp4", "business_loop.mp4", "lifestyle_loop.mp4"]
        for n_file in niche_names:
            local_clip = os.path.join(self.materials_dir, n_file)
            if os.path.exists(local_clip) and os.path.getsize(local_clip) > 50000:
                try:
                    cmd = [
                        ffmpeg_bin, "-y",
                        "-stream_loop", "-1",
                        "-i", local_clip,
                        "-t", str(duration_sec),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-an",
                        output_path,
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        return output_path
                except Exception as e:
                    logger.debug("Failed trimming local niche clip: %s", e)

        # 3. Fallback: Generate real procedural kinetic motion video
        return self.generate_procedural_motion_video(
            scene_type=scene_type,
            duration_sec=duration_sec,
            output_path=output_path,
            brand_color=brand_color,
        )

    def generate_procedural_motion_video(
        self,
        scene_type: str,
        duration_sec: float,
        output_path: str,
        brand_color: str = "#f5a623",
    ) -> str:
        """Generates real 30 FPS kinetic motion footage (particles, 3D cyber grid, neural nodes, scanlines)."""
        ffmpeg_bin = get_ffmpeg_binary()
        width, height = 1080, 1920
        fps = 30
        total_frames = max(30, int(duration_sec * fps))

        # Parse primary brand color
        b_hex = brand_color.lstrip("#")
        b_rgb = tuple(int(b_hex[i:i+2], 16) for i in (0, 2, 4)) if len(b_hex) == 6 else (245, 166, 35)

        cmd = [
            ffmpeg_bin, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-t", str(duration_sec),
            output_path,
        ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Neural network nodes for tech/revelation
        node_coords = [
            (int((math.sin(i * 1.3) * 0.4 + 0.5) * width), int((math.cos(i * 0.9) * 0.35 + 0.5) * height))
            for i in range(14)
        ]

        for frame_idx in range(total_frames):
            t = frame_idx / float(fps)
            img = Image.new("RGB", (width, height), color=(8, 12, 20))
            draw = ImageDraw.Draw(img)

            # 1. Perspective Cyber Grid moving downwards
            grid_speed = 75.0
            grid_offset = int((t * grid_speed) % 80)
            for y in range(grid_offset, height, 80):
                # Subtle depth brightness
                alpha_blend = int(18 + (y / height) * 22)
                draw.line([(0, y), (width, y)], fill=(alpha_blend, int(alpha_blend * 1.3), int(alpha_blend * 2.0)), width=1)
            for x in range(0, width, 80):
                draw.line([(x, 0), (x, height)], fill=(20, 28, 44), width=1)

            # 2. Dynamic Theme Visuals
            if scene_type in ("hook", "tension", "critical"):
                # Laser scanline sweeping down
                scan_y = int((t * 450) % height)
                draw.line([(0, scan_y), (width, scan_y)], fill=b_rgb, width=4)
                draw.line([(0, max(0, scan_y - 2)), (width, max(0, scan_y - 2))], fill=(255, 255, 255), width=2)

                # Floating glowing particles rising upwards
                for p in range(30):
                    px = int((math.sin(p * 2.1 + t * 0.9) * 0.45 + 0.5) * width)
                    py = int((height - ((p * 65 + t * 280) % height)))
                    radius = 5 + (p % 6)
                    draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=b_rgb)

            elif scene_type in ("revelation", "escalation", "core"):
                # Neural synaptic graph connecting with glowing animated pulses
                for idx, (nx, ny) in enumerate(node_coords):
                    # Wobble nodes smoothly
                    cx = nx + int(math.sin(t * 2.0 + idx) * 20)
                    cy = ny + int(math.cos(t * 1.8 + idx) * 20)
                    draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=b_rgb)
                    # Connect to adjacent nodes
                    next_node = node_coords[(idx + 1) % len(node_coords)]
                    draw.line([(cx, cy), next_node], fill=(int(b_rgb[0] * 0.35), int(b_rgb[1] * 0.35), int(b_rgb[2] * 0.35)), width=2)

                # Pulsing center radial wave
                wave_r = int((t * 260) % (width // 2))
                draw.ellipse(
                    [(width // 2) - wave_r, (height // 2) - wave_r, (width // 2) + wave_r, (height // 2) + wave_r],
                    outline=b_rgb,
                    width=2,
                )

            else:  # Payoff, CTA, Close
                # Animated rising candlestick bars / kinetic audio pillars
                for bar in range(18):
                    bx = 100 + (bar * 50)
                    bh = int(120 + math.sin(t * 4.0 + bar * 0.5) * 80 + math.cos(t * 2.5 + bar) * 40)
                    bh = max(30, min(350, bh))
                    draw.rounded_rectangle([bx, 1200 - bh, bx + 36, 1200], radius=6, fill=b_rgb)

                # Ambient floating sparkles
                for sp in range(25):
                    sx = int((math.sin(sp * 3.3 + t * 1.2) * 0.45 + 0.5) * width)
                    sy = int(((sp * 80 + t * 320) % height))
                    draw.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(255, 255, 255))

            proc.stdin.write(img.tobytes())

        proc.stdin.close()
        proc.wait()
        return output_path


material_service = MaterialService()

