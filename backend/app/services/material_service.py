import os
import re
import math
import subprocess
import json
import urllib.request
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw

from app.core.logging import get_logger
from app.schemas.video import StockMaterialItem
from app.services.visual_intelligence import visual_intelligence, SemanticDomain

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
        self.stock_images_dir = os.path.join(self.materials_dir, "stock_images")
        self.temp_dir = os.path.join(self.storage_dir, "temporary")

        os.makedirs(self.materials_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.stock_images_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def fetch_unsplash_stock_photo(
        self,
        keywords: List[str],
        access_key: Optional[str] = None,
        orientation: str = "portrait",
        result_idx: int = 0,
        scene_beat: str = "hook",
        worker_id: str = "general",
        topic: Optional[str] = None,
    ) -> Optional[str]:
        """Queries the Unsplash API for real, ultra-high-definition vertical photography matching keywords
        with domain intelligence, query transmutation, and negative keyword filtering to reject irrelevant assets."""
        key = access_key or os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
        if not key:
            try:
                from app.config import get_settings
                key = get_settings().unsplash_access_key
            except Exception:
                pass

        if not key or not keywords:
            return None

        # Clean keywords: strip #, quotes, brackets
        clean_kw = [k.replace('"', '').replace("'", '').replace("#", "").strip() for k in keywords if len(k.strip()) > 1]
        if not clean_kw:
            return None

        # 1. Classify Semantic Domain
        domain = visual_intelligence.classify_topic_domain(
            topic=topic or " ".join(clean_kw),
            worker_id=worker_id,
        )

        # 2. Build candidates: transmuted queries for gaming/tech, plus original clean keywords
        candidates: List[str] = []
        if domain in (SemanticDomain.GAMING_ESPORTS, SemanticDomain.AI_TECH, SemanticDomain.BUSINESS_FINANCE):
            transmuted = visual_intelligence.transmute_search_queries(
                domain=domain,
                scene_beat=scene_beat,
                original_keywords=clean_kw,
                scene_idx=result_idx,
            )
            candidates.extend(transmuted)

        # Also add original clean keywords if not already covered
        for kw in clean_kw:
            if kw.lower() not in [c.lower() for c in candidates]:
                candidates.append(kw)

        for candidate in candidates[:5]:
            try:
                query = urllib.parse.quote(candidate)
                url = f"https://api.unsplash.com/search/photos?query={query}&orientation={orientation}&per_page=8"
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Client-ID {key}", "User-Agent": "HIVE-VideoEngine/2.0"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    if not results:
                        continue

                    # Filter and score each result against negative terms and domain affinity
                    valid_photos = []
                    for photo in results:
                        is_valid, rel_score, reason = visual_intelligence.validate_photo_relevance(
                            domain=domain,
                            photo_meta=photo,
                            query=candidate,
                        )
                        if is_valid:
                            valid_photos.append((rel_score, photo))
                        else:
                            logger.debug("Filtered out Unsplash photo '%s': %s", photo.get("id"), reason)

                    if not valid_photos:
                        logger.info("All Unsplash results for candidate '%s' failed domain validation; trying next candidate", candidate)
                        continue

                    # Sort by relevance score descending
                    valid_photos.sort(key=lambda x: x[0], reverse=True)
                    selected_photo = valid_photos[result_idx % len(valid_photos)][1]

                    urls = selected_photo.get("urls", {})
                    img_url = urls.get("regular") or urls.get("full") or urls.get("small")
                    if img_url:
                        photo_id = selected_photo.get("id", "photo")
                        dest_path = os.path.join(self.downloads_dir, f"unsplash_{photo_id}.jpg")
                        if not os.path.exists(dest_path):
                            logger.info(
                                "Downloading verified Unsplash photo for domain '%s' (query='%s', score=%.2f): %s",
                                domain.value, candidate, valid_photos[0][0], photo_id
                            )
                            dl_req = urllib.request.Request(img_url, headers={"User-Agent": "HIVE-VideoEngine/2.0"})
                            with urllib.request.urlopen(dl_req, timeout=5.0) as dl_resp:
                                with open(dest_path, "wb") as f:
                                    f.write(dl_resp.read())
                        return dest_path
            except Exception as e:
                logger.debug("Unsplash candidate '%s' skipped: %s", candidate, e)

        return None

    def download_photo_by_url(self, img_url: str, photo_id: str) -> str:
        """Downloads an image from URL and stores it in the materials cache."""
        safe_id = "".join(c for c in photo_id if c.isalnum() or c in "-_") or "custom"
        dest_path = os.path.join(self.downloads_dir, f"unsplash_{safe_id}.jpg")
        if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1000:
            dl_req = urllib.request.Request(img_url, headers={"User-Agent": "HIVE-VideoEngine/2.0"})
            with urllib.request.urlopen(dl_req, timeout=8.0) as resp:
                with open(dest_path, "wb") as f:
                    f.write(resp.read())
        return dest_path

    def search_stock_library(
        self,
        query: str,
        orientation: str = "portrait",
        limit: int = 8,
        worker_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Searches live stock photography via Unsplash and local vault with domain-aware negative filtering."""
        clean_query = query.replace('"', '').replace("'", '').replace("#", "").strip()
        items: List[Dict[str, Any]] = []

        domain = visual_intelligence.classify_topic_domain(
            topic=topic or clean_query,
            worker_id=worker_id,
        )

        # 1. Unsplash live search
        key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
        if not key:
            try:
                from app.config import get_settings
                key = get_settings().unsplash_access_key
            except Exception:
                pass

        if key and clean_query:
            try:
                # If query contains brand name like 'fortnite' and domain is gaming, use transmuted query for higher yield
                effective_q = clean_query
                if domain == SemanticDomain.GAMING_ESPORTS and any(g in clean_query.lower() for g in ("fortnite", "roblox", "minecraft", "gta")):
                    effective_q = f"gaming setup {clean_query}"

                safe_q = urllib.parse.quote(effective_q)
                url = f"https://api.unsplash.com/search/photos?query={safe_q}&orientation={orientation}&per_page={limit * 2}"
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Client-ID {key}", "User-Agent": "HIVE-VideoEngine/2.0"}
                )
                with urllib.request.urlopen(req, timeout=4.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for r in data.get("results", []):
                        # Validate against negative domain terms
                        is_valid, rel_score, reason = visual_intelligence.validate_photo_relevance(
                            domain=domain,
                            photo_meta=r,
                            query=effective_q,
                        )
                        if not is_valid:
                            continue

                        urls = r.get("urls", {})
                        items.append({
                            "id": r.get("id"),
                            "title": r.get("alt_description") or r.get("description") or clean_query.title(),
                            "thumbnail_url": urls.get("small") or urls.get("thumb", ""),
                            "regular_url": urls.get("regular") or urls.get("full", ""),
                            "author": r.get("user", {}).get("name") or "Unsplash Contributor",
                            "source": "unsplash",
                            "relevance_score": rel_score,
                        })
                        if len(items) >= limit:
                            break
            except Exception as e:
                logger.debug("Unsplash search error: %s", e)

        # 2. Add matching local stock assets
        if os.path.exists(self.stock_images_dir):
            for fname in os.listdir(self.stock_images_dir):
                if any(ext in fname.lower() for ext in [".jpg", ".png", ".jpeg"]):
                    name_low = fname.lower()
                    matches = False
                    # Check token match or gaming domain match
                    if domain == SemanticDomain.GAMING_ESPORTS and "gaming" in name_low:
                        matches = True
                    elif any(w.lower() in name_low for w in clean_query.split()):
                        matches = True

                    if matches:
                        full_p = os.path.join(self.stock_images_dir, fname)
                        items.append({
                            "id": f"local-{fname}",
                            "title": fname.replace("_", " ").split(".")[0].title(),
                            "thumbnail_url": f"/api/materials/file?path={urllib.parse.quote(full_p)}",
                            "regular_url": full_p,
                            "author": "HIVE Stock Vault",
                            "source": "local_bank",
                            "relevance_score": 0.95,
                        })

        return items

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

                first_video = videos[0]
                video_files = first_video.get("video_files", [])
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

    def fetch_commons_stock_image(self, keywords: List[str]) -> Optional[str]:
        """Queries Wikimedia Commons for public domain stock photos matching scene keywords (100% free, no API key)."""
        if not keywords:
            return None

        clean_kw = [k.replace('"', '').replace("'", '').replace("#", "").strip() for k in keywords if len(k.strip()) > 1]
        if not clean_kw:
            return None

        candidates = [clean_kw[min(1, len(clean_kw)-1)], clean_kw[0]]
        for candidate in candidates:
            try:
                safe_query = urllib.parse.quote(f"{candidate} filetype:bitmap")
                url = (
                    f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                    f"&gsrsearch={safe_query}&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url|size&format=json"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "HIVE-Agent/1.0 (contact@hive-media.local)"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", {})
                    for _, page in pages.items():
                        ii_list = page.get("imageinfo", [])
                        if ii_list:
                            img_url = ii_list[0].get("url")
                            if img_url and any(img_url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                                fname = f"commons_{abs(hash(img_url)) % 10000000}.jpg"
                                dest = os.path.join(self.downloads_dir, fname)
                                if not os.path.exists(dest):
                                    dl_req = urllib.request.Request(img_url, headers={"User-Agent": "HIVE-Agent/1.0 (contact@hive-media.local)"})
                                    with urllib.request.urlopen(dl_req, timeout=4.0) as dl_resp:
                                        with open(dest, "wb") as f:
                                            f.write(dl_resp.read())
                                return dest
            except Exception as e:
                logger.debug("Wikimedia stock fetch error for '%s': %s", candidate, e)

        return None

    def convert_image_to_motion_video(
        self,
        image_path: str,
        duration_sec: float,
        output_path: str,
        motion_type: str = "zoom_in",
    ) -> bool:
        """Converts any real stock image into a smooth, cinematic 1080x1920 30FPS Ken Burns video clip with dynamic camera motion."""
        ffmpeg_bin = get_ffmpeg_binary()
        fps = 30
        frames_needed = max(30, int(duration_sec * fps))

        motion_filters = {
            "zoom_in": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0018,1.30)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "slow_zoom_in": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.25)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "pan_left": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='1.20':d={frames_needed}:x='(iw-iw/zoom)*(1-on/{frames_needed})':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "zoom_out": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='max(1.25-0.0015*on,1.0)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "slow_zoom_out": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='max(1.25-0.0015*on,1.0)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "pan_right": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='1.20':d={frames_needed}:x='(iw-iw/zoom)*(on/{frames_needed})':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "diagonal_drift": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0012,1.22)':d={frames_needed}:x='(iw-iw/zoom)*(0.2+0.6*(on/{frames_needed}))':y='(ih-ih/zoom)*(0.2+0.6*(on/{frames_needed}))':s=1080x1920:fps={fps}",
            "dramatic_zoom_in": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0012,1.18)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "pulse_zoom": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0022,1.28)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
            "ken_burns": f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.25)':d={frames_needed}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}",
        }

        vf = motion_filters.get(motion_type, motion_filters["zoom_in"])

        try:
            cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1",
                "-i", image_path,
                "-vf", vf,
                "-t", str(duration_sec),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-an",
                output_path,
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
        except Exception as e:
            logger.debug("Failed Ken Burns conversion: %s", e)
            return False

    def get_scene_footage(
        self,
        keywords: List[str],
        worker_id: str,
        scene_type: str,
        duration_sec: float,
        output_path: str,
        brand_color: str = "#00d4ff",
        scene_idx: int = 0,
        camera_motion: str = "",
    ) -> str:
        """Retrieves real stock video, downloads real stock photos with Ken Burns motion, or picks local assets."""
        res_path, _, _ = self.get_scene_footage_detailed(
            keywords=keywords,
            worker_id=worker_id,
            scene_type=scene_type,
            duration_sec=duration_sec,
            output_path=output_path,
            brand_color=brand_color,
            scene_idx=scene_idx,
            camera_motion=camera_motion,
        )
        return res_path

    def get_scene_footage_detailed(
        self,
        keywords: List[str],
        worker_id: str,
        scene_type: str,
        duration_sec: float,
        output_path: str,
        brand_color: str = "#00d4ff",
        scene_idx: int = 0,
        camera_motion: str = "",
        result_offset: int = 0,
    ) -> Tuple[str, str, str]:
        """Retrieves footage and returns (output_path, source_type, source_description) for full observability."""
        ffmpeg_bin = get_ffmpeg_binary()

        # Motion cadence: alternates across scenes for dynamic retention flow
        motion_sequence = ["zoom_in", "pan_left", "zoom_out", "pan_right", "diagonal_drift", "dramatic_zoom_in", "pulse_zoom"]
        effective_motion = camera_motion if camera_motion else motion_sequence[scene_idx % len(motion_sequence)]

        # Tier 0: Check Pre-Harvested Media Vault (Instant Local Hit)
        if result_offset == 0:
            try:
                from app.services.media_harvester import media_harvester
                vault_match = media_harvester.find_matching_footage(niche=worker_id, keywords=keywords)
                if vault_match and os.path.exists(vault_match):
                    # If image in vault, animate it with Ken Burns
                    if vault_match.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        if self.convert_image_to_motion_video(vault_match, duration_sec, output_path, motion_type=effective_motion):
                            logger.info("Using vault image with %s motion: %s", effective_motion, vault_match)
                            return output_path, "Media Vault", os.path.basename(vault_match)
                    else:
                        cmd = [
                            ffmpeg_bin, "-y",
                            "-stream_loop", "-1",
                            "-i", vault_match,
                            "-t", str(duration_sec),
                            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                            "-an",
                            output_path,
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                            logger.info("Using pre-harvested vault footage: %s", vault_match)
                            return output_path, "Media Vault", os.path.basename(vault_match)
            except Exception as e:
                logger.debug("Vault lookup skipped: %s", e)

        # Tier 1: Real Unsplash Stock Photography API (Priority 1)
        unsplash_img = self.fetch_unsplash_stock_photo(
            keywords=keywords,
            result_idx=result_offset,
            scene_beat=scene_type,
            worker_id=worker_id,
        )
        if unsplash_img and os.path.exists(unsplash_img):
            if self.convert_image_to_motion_video(unsplash_img, duration_sec, output_path, motion_type=effective_motion):
                logger.info("Using real Unsplash HD stock photo with %s motion: %s", effective_motion, unsplash_img)
                return output_path, "Unsplash 4K (Ken Burns)", os.path.basename(unsplash_img)

        # Tier 2: Real Pexels Stock Video API
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
                    logger.info("Using real Pexels stock video: %s", stock_path)
                    return output_path, "Pexels Stock Video", os.path.basename(stock_path)
            except Exception as e:
                logger.debug("Failed trimming stock footage: %s", e)

        # Tier 3: Real Wikimedia Commons Stock Photo with Ken Burns Camera Motion
        commons_img = self.fetch_commons_stock_image(keywords=keywords)
        if commons_img and os.path.exists(commons_img):
            if self.convert_image_to_motion_video(commons_img, duration_sec, output_path, motion_type=effective_motion):
                logger.info("Using real Wikimedia stock image with %s motion: %s", effective_motion, commons_img)
                return output_path, "Wikimedia Commons (Ken Burns)", os.path.basename(commons_img)

        # Tier 4: Curated Real Stock Asset Bank (niche-curated photos & videos on disk)
        chosen_asset, asset_type = self.find_best_local_stock_asset(
            keywords=keywords,
            worker_id=worker_id,
            scene_idx=scene_idx + result_offset,
        )
        asset_path = os.path.join(self.stock_images_dir, chosen_asset)

        if not os.path.exists(asset_path):
            asset_path = os.path.join(self.materials_dir, chosen_asset)

        if os.path.exists(asset_path) and os.path.getsize(asset_path) > 1000:
            if asset_type == "image":
                if self.convert_image_to_motion_video(asset_path, duration_sec, output_path, motion_type=effective_motion):
                    logger.info("Using curated real stock photo with %s motion: %s", effective_motion, asset_path)
                    return output_path, "Local Stock Asset Bank", chosen_asset
            elif asset_type == "video":
                try:
                    cmd = [
                        ffmpeg_bin, "-y",
                        "-stream_loop", "-1",
                        "-i", asset_path,
                        "-t", str(duration_sec),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-an",
                        output_path,
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        logger.info("Using curated real stock video: %s", asset_path)
                        return output_path, "Local Stock Asset Bank", chosen_asset
                except Exception as e:
                    logger.debug("Failed trimming curated video: %s", e)

        # Tier 4b: Fallback to ANY available real stock image before resorting to procedural graphics
        if os.path.exists(self.stock_images_dir):
            for candidate in os.listdir(self.stock_images_dir):
                if candidate.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    cand_path = os.path.join(self.stock_images_dir, candidate)
                    if os.path.exists(cand_path) and os.path.getsize(cand_path) > 1000:
                        if self.convert_image_to_motion_video(cand_path, duration_sec, output_path, motion_type=effective_motion):
                            logger.info("Using fallback real stock photo with %s motion: %s", effective_motion, cand_path)
                            return output_path, "Local Fallback Asset", candidate

        # Tier 5: Fallback to procedural kinetic motion video
        res_proc = self.generate_procedural_motion_video(
            scene_type=scene_type,
            duration_sec=duration_sec,
            output_path=output_path,
            brand_color=brand_color,
        )
        return res_proc, "Procedural Kinetic Neon Motion", f"{scene_type} {brand_color}"

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

    def find_best_local_stock_asset(
        self,
        keywords: List[str],
        worker_id: str = "tech",
        scene_idx: int = 0,
    ) -> Tuple[str, str]:
        """Intelligently matches local curated stock footage or photos from disk using domain classification,
        semantic keyword relevance, worker niche affinity, and scene rotation to guarantee accurate asset alignment."""
        available_files = []
        if os.path.exists(self.stock_images_dir):
            for f in sorted(os.listdir(self.stock_images_dir)):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4")):
                    available_files.append((f, os.path.join(self.stock_images_dir, f)))

        if not available_files and os.path.exists(self.materials_dir):
            for f in sorted(os.listdir(self.materials_dir)):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4")):
                    available_files.append((f, os.path.join(self.materials_dir, f)))

        if not available_files:
            return "tech_coding.jpg", "image"

        # 1. Classify Semantic Domain
        domain = visual_intelligence.classify_topic_domain(" ".join(keywords), worker_id=worker_id)

        # Normalize keywords and niche
        clean_tokens = set()
        for kw in keywords:
            for token in re.split(r"[\s,_\-]+", kw.lower()):
                token = re.sub(r"[^\w]", "", token)
                if len(token) > 2:
                    clean_tokens.add(token)

        worker_tokens = {worker_id.lower()}
        if domain == SemanticDomain.GAMING_ESPORTS or worker_id.lower() in ("entertainment", "culture"):
            worker_tokens.update([
                "gaming", "game", "esports", "controller", "streamer", "cyber", "arena",
                "battlestation", "rig", "pc", "console", "rgb", "keyboard", "arcade", "headset"
            ])
        if worker_id.lower() in ("lifestyle", "fashion"):
            worker_tokens.update(["fashion", "style", "luxury", "couture", "streetwear", "accessories", "runway", "model", "outfit"])
        elif worker_id.lower() in ("tech", "technology") or domain == SemanticDomain.AI_TECH:
            worker_tokens.update(["code", "coding", "software", "programmer", "server", "cyber", "ai", "data"])
        elif worker_id.lower() in ("business", "finance") or domain == SemanticDomain.BUSINESS_FINANCE:
            worker_tokens.update(["chart", "meeting", "office", "startup", "money", "growth"])
        elif worker_id.lower() in ("entertainment", "culture") and domain != SemanticDomain.GAMING_ESPORTS:
            worker_tokens.update(["cinema", "music", "concert", "stage", "movie", "film"])
        elif worker_id.lower() in ("curiosity", "education") or domain == SemanticDomain.CURIOSITY_SCIENCE:
            worker_tokens.update(["library", "science", "space", "nebula", "book", "galaxy"])

        scored = []
        for fname, full_path in available_files:
            name_lower = fname.lower()
            score = 0
            # Direct keyword match in filename
            for token in clean_tokens:
                if token in name_lower:
                    score += 10
            # Worker niche affinity
            for wt in worker_tokens:
                if wt in name_lower:
                    score += 5

            # Strong domain anchoring bonuses
            if domain == SemanticDomain.GAMING_ESPORTS and "gaming" in name_lower:
                score += 35
            elif domain == SemanticDomain.AI_TECH and any(k in name_lower for k in ("tech", "code", "server", "programmer")):
                score += 25
            elif domain == SemanticDomain.BUSINESS_FINANCE and any(k in name_lower for k in ("finance", "chart", "business")):
                score += 25
            elif domain == SemanticDomain.LIFESTYLE_FASHION and "fashion" in name_lower:
                score += 25

            scored.append((score, fname, full_path))

        # Filter to those with score > 0
        positive_matches = [item for item in scored if item[0] > 0]
        if positive_matches:
            positive_matches.sort(key=lambda x: x[0], reverse=True)
            chosen = positive_matches[scene_idx % len(positive_matches)]
            chosen_fname = chosen[1]
        else:
            # Fallback must respect domain, never pick random unrelated files
            domain_specific = []
            if domain == SemanticDomain.GAMING_ESPORTS:
                domain_specific = [f for f in available_files if "gaming" in f[0].lower()]
            elif domain == SemanticDomain.AI_TECH:
                domain_specific = [f for f in available_files if any(k in f[0].lower() for k in ("tech", "code", "server", "programmer"))]
            elif domain == SemanticDomain.BUSINESS_FINANCE:
                domain_specific = [f for f in available_files if any(k in f[0].lower() for k in ("finance", "chart", "business"))]
            elif domain == SemanticDomain.LIFESTYLE_FASHION:
                domain_specific = [f for f in available_files if "fashion" in f[0].lower()]
            elif domain == SemanticDomain.ENTERTAINMENT_CINEMA:
                domain_specific = [f for f in available_files if any(k in f[0].lower() for k in ("entertainment", "concert", "cinema"))]

            if domain_specific:
                chosen_fname = domain_specific[scene_idx % len(domain_specific)][0]
            else:
                chosen_fname = available_files[scene_idx % len(available_files)][0]

        is_video = chosen_fname.lower().endswith(".mp4")
        return chosen_fname, "video" if is_video else "image"

    def list_stock_materials(self, worker_id: Optional[str] = None) -> List[StockMaterialItem]:
        """Returns all available stock images and motion clips in the library."""
        items: List[StockMaterialItem] = []
        # Check stock_images_dir
        if os.path.exists(self.stock_images_dir):
            for fname in sorted(os.listdir(self.stock_images_dir)):
                if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4")):
                    fpath = os.path.join(self.stock_images_dir, fname)
                    is_vid = fname.lower().endswith(".mp4")
                    parts = re.split(r"[_\-.]+", fname.lower())
                    niche = "tech"
                    for n in ["fashion", "lifestyle", "business", "tech", "entertainment", "education", "curiosity", "finance"]:
                        if n in parts:
                            niche = n
                            break
                    tags = [p for p in parts if len(p) > 2 and p not in ("jpg", "jpeg", "png", "webp", "mp4")]
                    rel_url = f"/storage/materials/stock_images/{fname}"
                    thumb_url = rel_url if not is_vid else f"/storage/materials/stock_images/{fname.replace('.mp4', '.jpg')}"
                    items.append(
                        StockMaterialItem(
                            filename=fname,
                            asset_type="video" if is_vid else "image",
                            file_path=fpath,
                            relative_url=rel_url,
                            thumbnail_url=thumb_url,
                            niche=niche,
                            tags=tags,
                        )
                    )

        # Check downloads_dir
        if os.path.exists(self.downloads_dir):
            for fname in sorted(os.listdir(self.downloads_dir)):
                if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4")):
                    fpath = os.path.join(self.downloads_dir, fname)
                    is_vid = fname.lower().endswith(".mp4")
                    rel_url = f"/storage/materials/downloads/{fname}"
                    items.append(
                        StockMaterialItem(
                            filename=fname,
                            asset_type="video" if is_vid else "image",
                            file_path=fpath,
                            relative_url=rel_url,
                            thumbnail_url=rel_url,
                            niche="general",
                            tags=["unsplash", "downloaded"],
                        )
                    )

        if worker_id:
            filtered = [item for item in items if item.niche == worker_id or worker_id in item.tags]
            if filtered:
                return filtered

        return items


material_service = MaterialService()

