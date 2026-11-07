import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.video_engine import video_engine
from app.services.video_renderer import video_renderer
from app.services.material_service import material_service
from app.services.sfx_service import sfx_service
from app.schemas.video import SceneUpdateRequest


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
    items = material_service.list_stock_materials()
    assert len(items) > 0
    assert any("fashion" in item.filename.lower() for item in items)


def test_natural_speech_duration_matching(tmp_path):
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
    blueprint = video_engine.assemble_blueprint(
        worker_id="lifestyle",
        trend_title="Future of Cyber Fashion 2025",
        hook_text="Digital fashion and runway tech.",
        body_points=["Wearable art is revolutionizing fashion."],
        cta_text="Follow for more.",
        description="Digital fashion showcase.",
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

    # 4. Test GET clips
    clips_data = video_renderer.get_scene_clips(bp.blueprint_id)
    assert len(clips_data) == len(bp.scenes)
    assert clips_data[0].scene_idx == 0

    # 5. Test Regenerating Single Scene with bottom caption and color
    req = SceneUpdateRequest(
        voiceover_text="Updated voiceover for Scene 1 with bottom subtitles.",
        search_keywords=["fashion", "runway", "model"],
        camera_motion="pan_left",
        caption_position="bottom",
        caption_highlight_color="#00FF66",
        caption_font_size=64,
        caption_style="pill",
        voice_speed=1.15,
        bgm_track="cyber_beat",
        visual_filter="vibrant",
    )
    regen_job = video_renderer.render_single_scene(
        blueprint_id=bp.blueprint_id,
        scene_idx=1,
        update=req,
    )
    assert regen_job.status == "complete"

    # Verify Scene 1 was updated in the returned clips
    updated_clip = next(c for c in regen_job.scene_clips if c.scene_idx == 1)
    assert updated_clip.voiceover_text == "Updated voiceover for Scene 1 with bottom subtitles."
    assert updated_clip.camera_motion == "pan_left"

    # 6. Test Reorder Scenes: Move scene 0 to index 2
    initial_count = len(job.scene_clips)
    reorder_job = video_renderer.reorder_scenes(
        blueprint_id=bp.blueprint_id,
        from_idx=0,
        to_idx=2,
    )
    assert reorder_job.status == "complete"

    # 7. Test Duplicate Scene: Duplicate scene 0
    dup_job = video_renderer.duplicate_scene(
        blueprint_id=bp.blueprint_id,
        scene_idx=0,
    )
    assert dup_job.status == "complete"
    assert len(dup_job.scene_clips) == initial_count + 1

    # 8. Test Delete Scene: Delete the duplicate
    del_job = video_renderer.delete_scene(
        blueprint_id=bp.blueprint_id,
        scene_idx=1,
    )
    assert del_job.status == "complete"
    assert len(del_job.scene_clips) == initial_count

    # Verify master video is still intact
    final_mp4 = os.path.join("storage", "videos", f"{bp.blueprint_id}.mp4")
    assert os.path.exists(final_mp4)
    assert os.path.getsize(final_mp4) > 10000


def test_sfx_catalog_endpoint():
    catalog = sfx_service.list_available_sfx()
    assert len(catalog) >= 8
    cue_ids = [item["id"] for item in catalog]
    assert "whoosh" in cue_ids
    assert "impact" in cue_ids
    assert "pop" in cue_ids
    assert "chime" in cue_ids
    assert "riser" in cue_ids
    assert "glitch" in cue_ids
    assert "cash_register" in cue_ids
    assert "camera_click" in cue_ids


def test_enhance_script_endpoint():
    bp = video_engine.assemble_blueprint(
        worker_id="lifestyle",
        trend_title="AI Script Booster Test",
        hook_text="This is a simple script text.",
        body_points=["Here is a fact."],
        cta_text="Subscribe now.",
        description="Testing script booster endpoint.",
    )
    video_renderer.blueprints[bp.blueprint_id] = bp

    enhanced = video_engine.enhance_script_sync(
        current_text="This is a simple script text.",
        emotional_beat="hook",
        style="punchy",
    )
    assert len(enhanced) > 0


def test_stock_library_search():
    results = material_service.search_stock_library(query="cyberpunk neon", orientation="portrait", limit=6)
    assert len(results) > 0
    first = results[0]
    assert first["thumbnail_url"] is not None
    assert first["regular_url"] is not None
    assert first["source"] in ("unsplash", "stock_materials")


def test_scene_visual_reroll_and_custom_asset():
    bp = video_engine.assemble_blueprint(
        worker_id="tech",
        trend_title="Re-roll Test Blueprint",
        hook_text="AI breakthrough test for visual reroll.",
        body_points=["Scene testing re-roll visual cycling."],
        cta_text="Subscribe.",
        description="Verifying visual reroll cycling and custom asset updates.",
    )
    video_renderer.blueprints[bp.blueprint_id] = bp
    init_job = video_renderer.render_blueprint(bp)
    assert init_job.status == "complete"

    clip_before = init_job.scene_clips[0]

    # Re-roll scene 0 visual
    reroll_job = video_renderer.render_single_scene(
        blueprint_id=bp.blueprint_id,
        scene_idx=0,
        update=SceneUpdateRequest(reroll_visual=True),
    )
    assert reroll_job.status == "complete"
    clip_after = reroll_job.scene_clips[0]
    assert clip_after.clip_path.endswith(".mp4")
    assert os.path.exists(os.path.join("storage", "clips", bp.blueprint_id, "scene_0.mp4"))

    # Custom asset update
    stock_items = material_service.list_stock_materials()
    if stock_items:
        custom_file = stock_items[0].file_path
        update_job = video_renderer.render_single_scene(
            blueprint_id=bp.blueprint_id,
            scene_idx=0,
            update=SceneUpdateRequest(custom_asset_path=custom_file),
        )
        assert update_job.status == "complete"


@pytest.mark.anyio
async def test_regenerate_blueprint_script_api():
    import json
    from app.api.routes import regenerate_blueprint_script_endpoint
    from unittest.mock import MagicMock, AsyncMock

    bp = video_engine.assemble_blueprint(
        worker_id="tech",
        trend_title="Next-Gen Robotics Fleet Deployed",
        hook_text="Old hook text.",
        body_points=["Old point 1", "Old point 2"],
        cta_text="Old cta.",
        description="Old description.",
    )
    video_renderer.blueprints[bp.blueprint_id] = bp

    mock_llm = MagicMock()
    mock_llm.model = "llama3.1"
    mock_llm.timeout = 100.0
    mock_llm.generate = AsyncMock(return_value=json.dumps({
        "hook": "Robotics just changed manufacturing forever.",
        "cta": "Follow for more robotics engineering updates.",
        "description": "How autonomous factory fleets are setting new output records.",
        "scenes": [
            {"scene_idx": 0, "beat": "hook", "voiceover": "Robotics just changed manufacturing forever.", "visual_description": "Robots working", "search_keywords": ["robot arm", "factory"], "camera_motion": "slow_zoom_in", "sfx_cue": "impact"},
            {"scene_idx": 1, "beat": "tension", "voiceover": "Legacy factories can no longer match this operational velocity.", "visual_description": "Factory line", "search_keywords": ["conveyor", "manufacturing"], "camera_motion": "pan_left", "sfx_cue": "suspense_sting"},
            {"scene_idx": 2, "beat": "revelation", "voiceover": "New neural control systems allow instant adaptation to any part geometry.", "visual_description": "Precision laser", "search_keywords": ["laser", "engineering"], "camera_motion": "slow_zoom_in", "sfx_cue": "reveal_chime"},
            {"scene_idx": 3, "beat": "escalation", "voiceover": "Error rates have plunged by over ninety-five percent across pilot runs.", "visual_description": "Quality screen", "search_keywords": ["inspection", "screen"], "camera_motion": "pan_right", "sfx_cue": "whoosh"},
            {"scene_idx": 4, "beat": "deep_dive", "voiceover": "Engineers no longer write custom kinematics; they train reward functions.", "visual_description": "Neural net", "search_keywords": ["ai code", "datacenter"], "camera_motion": "slow_zoom_out", "sfx_cue": None},
            {"scene_idx": 5, "beat": "twist", "voiceover": "The real surprise is the total capital expenditure payback window.", "visual_description": "Financial graph", "search_keywords": ["roi", "finance"], "camera_motion": "slow_zoom_in", "sfx_cue": "impact"},
            {"scene_idx": 6, "beat": "payoff", "voiceover": "Payback is achieved in under seven months instead of three years.", "visual_description": "Modern plant", "search_keywords": ["clean room", "future"], "camera_motion": "ken_burns", "sfx_cue": "reveal_chime"},
            {"scene_idx": 7, "beat": "cta", "voiceover": "Follow for daily breakthroughs in robotics and hardware engineering.", "visual_description": "Brand outro", "search_keywords": ["robotics logo", "dark studio"], "camera_motion": "slow_zoom_in", "sfx_cue": "whoosh"}
        ]
    }))

    updated = await regenerate_blueprint_script_endpoint(
        blueprint_id=bp.blueprint_id,
        llm=mock_llm,
    )
    assert updated.blueprint_id == bp.blueprint_id
    assert updated.hook_variants[0].hook_text if updated.hook_variants else True
    assert updated.scenes[0].audio.voiceover_text == "Robotics just changed manufacturing forever."
    assert updated.scenes[6].audio.voiceover_text == "Payback is achieved in under seven months instead of three years."


@pytest.mark.anyio
async def test_stream_blueprint_generation_endpoint():
    import json
    from app.api.routes import stream_generate_blueprint_endpoint, VideoBlueprintRequest
    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    mock_llm.model = "llama3.1"
    mock_llm.timeout = 60.0

    async def mock_stream(*args, **kwargs):
        chunks = ['{"hook": "Stream Hook", ', '"cta": "Stream CTA", ', '"description": "Stream Desc", ', '"scenes": [',
                  '{"voiceover": "S1", "visual_description": "V1", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_in"},',
                  '{"voiceover": "S2", "visual_description": "V2", "search_keywords": ["k1", "k2"], "camera_motion": "pan_left"},',
                  '{"voiceover": "S3", "visual_description": "V3", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_in"},',
                  '{"voiceover": "S4", "visual_description": "V4", "search_keywords": ["k1", "k2"], "camera_motion": "pan_right"},',
                  '{"voiceover": "S5", "visual_description": "V5", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_out"},',
                  '{"voiceover": "S6", "visual_description": "V6", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_in"},',
                  '{"voiceover": "S7", "visual_description": "V7", "search_keywords": ["k1", "k2"], "camera_motion": "ken_burns"},',
                  '{"voiceover": "S8", "visual_description": "V8", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_in"}]}'
        ]
        for c in chunks:
            yield c

    mock_llm.generate_stream = mock_stream

    req = VideoBlueprintRequest(
        worker_id="tech",
        trend_title="Streaming Execution Architecture",
        trend_summary="Real-time agentic trace streaming verification.",
    )

    response = await stream_generate_blueprint_endpoint(req=req, llm=mock_llm)
    assert response.media_type == "text/event-stream"

    # Read SSE events from streaming body
    events_received = []
    async for chunk in response.body_iterator:
        text = chunk if isinstance(chunk, str) else chunk.decode("utf-8")
        events_received.append(text)

    full_stream_text = "".join(events_received)
    assert "data: " in full_stream_text
    assert '"type": "step"' in full_stream_text
    assert '"type": "complete"' in full_stream_text
    assert '"blueprint"' in full_stream_text



