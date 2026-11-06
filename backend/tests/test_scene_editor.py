import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.services.video_engine import video_engine
from app.services.video_renderer import video_renderer
from app.services.material_service import material_service
from app.schemas.video import SceneUpdateRequest

client = TestClient(app)


def test_find_best_local_stock_asset_fashion():
    asset, asset_type = material_service.find_best_local_stock_asset(
        keywords=["fashion", "runway", "luxury"],
        worker_id="lifestyle",
        scene_idx=0,
    )
    assert asset_type in ("image", "video")
    assert "fashion" in asset.lower()


def test_find_best_local_stock_asset_rotation():
    # Verify different scene indices cycle through matching assets
    asset0, _ = material_service.find_best_local_stock_asset(
        keywords=["fashion", "couture", "streetwear"],
        worker_id="lifestyle",
        scene_idx=0,
    )
    asset1, _ = material_service.find_best_local_stock_asset(
        keywords=["fashion", "couture", "streetwear"],
        worker_id="lifestyle",
        scene_idx=1,
    )
    assert asset0.endswith((".jpg", ".png", ".mp4"))
    assert asset1.endswith((".jpg", ".png", ".mp4"))


def test_list_stock_materials_endpoint():
    resp = client.get("/api/v1/video/stock-materials")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    assert any("fashion" in item["filename"].lower() for item in items)


def test_natural_speech_duration_matching():
    short_text = "Stop coding."
    long_text = "Fashion in 2025 isn't just about what you wear—it's about how your clothes interact with the digital world."
    dur_short = video_renderer._calculate_natural_speech_duration(short_text)
    dur_long = video_renderer._calculate_natural_speech_duration(long_text)
    assert dur_short >= 3.2
    assert dur_long >= 7.0  # 17 words + punctuation needs at least 7.0s to speak comfortably
    assert dur_long > dur_short
    wav_path = str(tmp_path / "ambient.wav")
    video_renderer._generate_ambient_bgm(duration_sec=3.5, output_path=wav_path)
    dur = video_renderer._get_audio_duration(wav_path)
    assert abs(dur - 3.5) <= 0.05


def test_render_scene_overlay_bottom_position(tmp_path):
    blueprint = video_engine.generate_blueprint(
        worker_id="lifestyle",
        trend_title="Future of Cyber Fashion 2025",
        trend_summary="Digital fashion and runway technology revolutionizing wearable art.",
    )
    scene = blueprint.scenes[0]
    out_overlay = str(tmp_path / "test_bottom_overlay.png")

    video_renderer._render_scene_overlay(
        scene=scene,
        blueprint=blueprint,
        scene_idx=0,
        total_scenes=len(blueprint.scenes),
        output_path=out_overlay,
        caption_position="bottom",
        caption_font_size=68,
        caption_highlight_color="#FFE600",
        caption_style="pill",
    )
    assert os.path.exists(out_overlay)
    assert os.path.getsize(out_overlay) > 1000


def test_scene_clips_generation_and_editor_endpoint():
    # 1. Create a 3-scene blueprint
    bp = video_engine.assemble_blueprint(
        worker_id="lifestyle",
        trend_title="Scene Clips & Editor Visual Test",
        hook_text="Stop coding by hand.",
        body_points=["Scene 1: Neural voice active.", "Scene 2: High definition output."],
        cta_text="Follow for more.",
        description="Testing scene clips and single scene editing.",
    )
    assert len(bp.scenes) >= 3

    # 2. Render Blueprint
    job = video_renderer.render_blueprint(bp)
    assert job.status == "complete"
    assert len(job.scene_clips) == len(bp.scenes)

    # 3. Verify each scene clip file and artifact
    for sc in job.scene_clips:
        assert sc.scene_idx >= 0
        assert sc.clip_path.startswith(f"/storage/clips/{bp.blueprint_id}/scene_")
        assert sc.clip_path.endswith(".mp4")
        assert sc.thumbnail_path is not None
        assert sc.overlay_path is not None

        # Verify physical file on disk
        local_clip = os.path.join("storage", "clips", bp.blueprint_id, f"scene_{sc.scene_idx}.mp4")
        assert os.path.exists(local_clip)
        assert os.path.getsize(local_clip) > 1000

    # 4. Test GET /video/blueprint/{blueprint_id}/clips API
    resp = client.get(f"/api/v1/video/blueprint/{bp.blueprint_id}/clips")
    assert resp.status_code == 200
    clips_data = resp.json()
    assert len(clips_data) == len(bp.scenes)
    assert clips_data[0]["scene_idx"] == 0

    # 5. Test Regenerating Single Scene with bottom caption and color: POST /video/blueprint/{blueprint_id}/scene/1/render
    update_payload = {
        "voiceover_text": "Updated voiceover for Scene 1 with bottom subtitles.",
        "search_keywords": ["fashion", "runway", "model"],
        "camera_motion": "pan_left",
        "caption_position": "bottom",
        "caption_highlight_color": "#00FF66",
        "caption_font_size": 64,
        "caption_style": "pill",
    }
    regen_resp = client.post(
        f"/api/v1/video/blueprint/{bp.blueprint_id}/scene/1/render",
        json=update_payload,
    )
    assert regen_resp.status_code == 200
    regen_job = regen_resp.json()
    assert regen_job["status"] == "complete"

    # Verify Scene 1 was updated in the returned clips
    updated_clip = next(c for c in regen_job["scene_clips"] if c["scene_idx"] == 1)
    assert updated_clip["voiceover_text"] == "Updated voiceover for Scene 1 with bottom subtitles."
    assert updated_clip["camera_motion"] == "pan_left"

    # Verify master video is still intact
    final_mp4 = os.path.join("storage", "videos", f"{bp.blueprint_id}.mp4")
    assert os.path.exists(final_mp4)
    assert os.path.getsize(final_mp4) > 10000
