import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.services.video_engine import video_engine
from app.services.video_renderer import video_renderer
from app.schemas.video import SceneUpdateRequest

client = TestClient(app)


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

    # 5. Test Regenerating Single Scene: POST /video/blueprint/{blueprint_id}/scene/1/render
    update_payload = {
        "voiceover_text": "Updated voiceover for Scene 1 with neural speech.",
        "search_keywords": ["fashion", "runway", "model"],
        "camera_motion": "pan_left",
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
    assert updated_clip["voiceover_text"] == "Updated voiceover for Scene 1 with neural speech."
    assert updated_clip["camera_motion"] == "pan_left"

    # Verify master video is still intact
    final_mp4 = os.path.join("storage", "videos", f"{bp.blueprint_id}.mp4")
    assert os.path.exists(final_mp4)
    assert os.path.getsize(final_mp4) > 10000

