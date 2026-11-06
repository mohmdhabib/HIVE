import os
import json
import uuid
import subprocess
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger("media_harvester")


def get_ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"


class VaultAsset(BaseModel):
    asset_id: str
    niche: str
    filename: str
    asset_type: str  # "video" | "image"
    file_path: str
    relative_url: str
    thumbnail_url: Optional[str] = None
    tags: List[str]
    duration_sec: float
    width: int
    height: int
    source: str
    created_at: str


class HarvestRequest(BaseModel):
    niche: str = "tech"
    query_or_url: Optional[str] = None
    count: int = 3
    tags: Optional[List[str]] = None


class MediaHarvesterService:
    """Automated media harvesting pipeline for downloading, cutting, and caching vertical B-roll assets."""

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.storage_dir = os.path.join(base_dir, "storage")
        if not os.path.exists(self.storage_dir):
            if os.path.exists("/app/storage"):
                self.storage_dir = "/app/storage"
            elif os.path.exists(os.path.join(base_dir, "..", "storage")):
                self.storage_dir = os.path.abspath(os.path.join(base_dir, "..", "storage"))

        self.vault_dir = os.path.join(self.storage_dir, "materials", "vault")
        self.temp_dir = os.path.join(self.storage_dir, "temporary")
        self.manifest_file = os.path.join(self.vault_dir, "vault_manifest.json")

        os.makedirs(self.vault_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # Ensure niche folders
        for niche in ("tech", "business", "curiosity", "lifestyle", "entertainment"):
            os.makedirs(os.path.join(self.vault_dir, niche), exist_ok=True)

        self._load_manifest()

    def _load_manifest(self):
        self.assets: Dict[str, VaultAsset] = {}
        if os.path.exists(self.manifest_file):
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("assets", []):
                        asset = VaultAsset(**item)
                        if os.path.exists(asset.file_path):
                            self.assets[asset.asset_id] = asset
            except Exception as e:
                logger.debug("Failed loading vault manifest: %s", e)

    def _save_manifest(self):
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump({"assets": [a.model_dump() for a in self.assets.values()]}, f, indent=2)
        except Exception as e:
            logger.error("Failed saving vault manifest: %s", e)

    def list_vault_assets(self, niche: Optional[str] = None) -> List[VaultAsset]:
        """Returns all registered vault assets, optionally filtered by niche."""
        if niche:
            return [a for a in self.assets.values() if a.niche == niche]
        return list(self.assets.values())

    def find_matching_footage(self, niche: str, keywords: List[str]) -> Optional[str]:
        """Finds the most relevant pre-cached vertical video in the vault matching scene keywords."""
        if not keywords:
            candidates = [a for a in self.assets.values() if a.niche == niche]
            return candidates[0].file_path if candidates else None

        kw_lower = set(k.lower().strip(".,!?:") for k in keywords if len(k) > 1)
        best_asset = None
        best_score = -1

        for asset in self.assets.values():
            if asset.niche == niche or asset.niche == "general":
                score = 0
                for tag in asset.tags:
                    if tag.lower() in kw_lower:
                        score += 2
                    for kw in kw_lower:
                        if kw in tag.lower() or tag.lower() in kw:
                            score += 1
                if score > best_score:
                    best_score = score
                    best_asset = asset

        if best_asset and best_score > 0 and os.path.exists(best_asset.file_path):
            logger.info("Found matching vault footage '%s' with score %d", best_asset.filename, best_score)
            return best_asset.file_path

        # If no tag match but niche assets exist, cycle through niche assets
        niche_assets = [a for a in self.assets.values() if a.niche == niche and os.path.exists(a.file_path)]
        if niche_assets:
            return niche_assets[0].file_path

        return None

    def harvest_from_url(
        self,
        url: str,
        niche: str = "tech",
        custom_tags: Optional[List[str]] = None,
        max_duration_sec: float = 24.0,
        segment_len_sec: float = 4.0,
    ) -> List[VaultAsset]:
        """Harvests a vertical or horizontal video from YouTube / web URL using yt-dlp, trims and normalizes to 1080x1920 clips."""
        ffmpeg_bin = get_ffmpeg_binary()
        created_assets = []
        raw_download_path = os.path.join(self.temp_dir, f"raw_{uuid.uuid4().hex[:8]}.mp4")

        try:
            import yt_dlp
            logger.info("Starting yt-dlp harvest from URL: %s", url)

            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": raw_download_path,
                "quiet": True,
                "no_warnings": True,
                "max_filesize": 50 * 1024 * 1024,  # 50MB limit
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Harvested Footage")
                tags = custom_tags or [t.lower() for t in info.get("tags", [])[:5]] or [niche, "footage", "broll"]

            if not os.path.exists(raw_download_path):
                # Check with possible extension
                for ext in (".mp4", ".mkv", ".webm"):
                    alt = raw_download_path.replace(".mp4", ext)
                    if os.path.exists(alt):
                        raw_download_path = alt
                        break

            if os.path.exists(raw_download_path):
                # Cut into multiple bite-sized 4s vertical clips
                num_segments = max(1, min(4, int(max_duration_sec // segment_len_sec)))
                niche_dir = os.path.join(self.vault_dir, niche)

                for seg_idx in range(num_segments):
                    start_time = seg_idx * segment_len_sec
                    asset_id = f"vlt-{niche}-{uuid.uuid4().hex[:8]}"
                    clip_filename = f"{asset_id}.mp4"
                    clip_dest = os.path.join(niche_dir, clip_filename)
                    thumb_filename = f"{asset_id}_thumb.jpg"
                    thumb_dest = os.path.join(niche_dir, thumb_filename)

                    # Normalize, crop to 1080x1920, and strip audio
                    cut_cmd = [
                        ffmpeg_bin, "-y",
                        "-ss", str(start_time),
                        "-i", raw_download_path,
                        "-t", str(segment_len_sec),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-an",
                        clip_dest,
                    ]
                    subprocess.run(cut_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                    # Extract thumbnail
                    thumb_cmd = [
                        ffmpeg_bin, "-y",
                        "-ss", "00:00:00.5",
                        "-i", clip_dest,
                        "-vframes", "1",
                        thumb_dest,
                    ]
                    subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    if os.path.exists(clip_dest) and os.path.getsize(clip_dest) > 1000:
                        asset = VaultAsset(
                            asset_id=asset_id,
                            niche=niche,
                            filename=clip_filename,
                            asset_type="video",
                            file_path=clip_dest,
                            relative_url=f"/storage/materials/vault/{niche}/{clip_filename}",
                            thumbnail_url=f"/storage/materials/vault/{niche}/{thumb_filename}",
                            tags=tags,
                            duration_sec=segment_len_sec,
                            width=1080,
                            height=1920,
                            source="yt-dlp",
                            created_at=datetime.now(timezone.utc).isoformat(),
                        )
                        self.assets[asset_id] = asset
                        created_assets.append(asset)

                self._save_manifest()
                logger.info("Harvested %d vertical clips from %s into vault", len(created_assets), url)

        except Exception as e:
            logger.exception("Failed harvesting from URL %s: %s", url, e)

        finally:
            if os.path.exists(raw_download_path):
                try:
                    os.remove(raw_download_path)
                except Exception:
                    pass

        return created_assets

    def harvest_stock_batch(self, niche: str = "tech", count: int = 4) -> List[VaultAsset]:
        """Harvests stock visuals from Unsplash & Wikimedia into the vault, pre-rendered with Ken Burns motion."""
        from app.services.material_service import material_service
        ffmpeg_bin = get_ffmpeg_binary()

        niche_queries = {
            "tech": ["developer terminal code", "server datacenter lights", "ai neural network", "cyber security matrix"],
            "business": ["stock trading charts", "corporate skyscraper office", "executive boardroom meeting", "financial investment growth"],
            "curiosity": ["deep space nebula galaxy", "quantum science laboratory", "holographic digital brain", "astronomy starfield"],
            "lifestyle": ["minimalist modern aesthetic coffee", "fitness runner athletic golden hour", "coastal road sunset drive"],
            "entertainment": ["concert stage neon lights", "professional cinema camera", "electronic music festival"],
        }

        queries = niche_queries.get(niche, niche_queries["tech"])[:count]
        created_assets = []
        niche_dir = os.path.join(self.vault_dir, niche)

        for q in queries:
            kw = q.split()
            # 1. Try Unsplash, then Wikimedia
            img_path = material_service.fetch_unsplash_stock_photo(kw)
            if not img_path:
                img_path = material_service.fetch_commons_stock_image(kw)

            if img_path and os.path.exists(img_path):
                asset_id = f"vlt-{niche}-{uuid.uuid4().hex[:8]}"
                mp4_filename = f"{asset_id}.mp4"
                mp4_dest = os.path.join(niche_dir, mp4_filename)
                thumb_filename = f"{asset_id}_thumb.jpg"
                thumb_dest = os.path.join(niche_dir, thumb_filename)

                # Render Ken Burns motion
                if material_service.convert_image_to_motion_video(img_path, duration_sec=4.5, output_path=mp4_dest):
                    # Thumbnail
                    thumb_cmd = [
                        ffmpeg_bin, "-y",
                        "-ss", "00:00:00.5",
                        "-i", mp4_dest,
                        "-vframes", "1",
                        thumb_dest,
                    ]
                    subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    asset = VaultAsset(
                        asset_id=asset_id,
                        niche=niche,
                        filename=mp4_filename,
                        asset_type="video",
                        file_path=mp4_dest,
                        relative_url=f"/storage/materials/vault/{niche}/{mp4_filename}",
                        thumbnail_url=f"/storage/materials/vault/{niche}/{thumb_filename}",
                        tags=kw,
                        duration_sec=4.5,
                        width=1080,
                        height=1920,
                        source="automated_harvester",
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                    self.assets[asset_id] = asset
                    created_assets.append(asset)

        if created_assets:
            self._save_manifest()
            logger.info("Batch harvested %d assets for niche '%s'", len(created_assets), niche)

        return created_assets


media_harvester = MediaHarvesterService()

