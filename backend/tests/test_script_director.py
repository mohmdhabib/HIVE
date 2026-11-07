import pytest
from app.services.script_director import script_director_agent
from app.workers.registry import get_worker
from app.schemas.video import SceneNode, GenerationTelemetry


@pytest.mark.anyio
async def test_script_director_crafts_unique_screenplays():
    worker = get_worker("tech")
    assert worker is not None

    # Test two very different trends
    trend_a_title = "OpenAI Unveils Autonomous Reasoning Architecture 5.0"
    trend_a_summary = "A breakthrough new AI architecture operates with zero human supervision."

    trend_b_title = "Hidden Cloud Licensing Fees Drain Enterprise AI Budgets"
    trend_b_summary = "Unchecked token API calls and egress costs cause massive unexpected bills."

    scenes_a, hook_a, cta_a, desc_a, telem_a = await script_director_agent.craft_screenplay(
        worker=worker,
        trend_title=trend_a_title,
        trend_summary=trend_a_summary,
        llm=None,  # Tests autonomous NLP fallback engine
    )

    scenes_b, hook_b, cta_b, desc_b, telem_b = await script_director_agent.craft_screenplay(
        worker=worker,
        trend_title=trend_b_title,
        trend_summary=trend_b_summary,
        llm=None,
    )

    # 1. Verify 8 scenes each
    assert len(scenes_a) >= 7
    assert len(scenes_b) >= 7

    # 2. Verify all scenes are valid SceneNodes
    for s in scenes_a + scenes_b:
        assert isinstance(s, SceneNode)
        assert s.visual.camera_motion in {"static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "ken_burns"}
        assert len(s.visual.search_keywords) >= 2
        assert len(s.audio.voiceover_text) > 10

    # 3. Verify scripts are NOT identical
    assert hook_a != hook_b
    assert scenes_a[0].audio.voiceover_text != scenes_b[0].audio.voiceover_text
    assert scenes_a[1].audio.voiceover_text != scenes_b[1].audio.voiceover_text

    # 4. Verify telemetry output
    assert isinstance(telem_a, GenerationTelemetry)
    assert telem_a.screenplay_archetype != ""
    assert len(telem_a.event_trace) >= 3
    assert any("Synthesizing unique" in e.get("message", "") for e in telem_a.event_trace)


@pytest.mark.anyio
async def test_script_director_camera_motion_sanitization():
    worker = get_worker("tech")
    scenes, _, _, _, _ = await script_director_agent.craft_screenplay(
        worker=worker,
        trend_title="Quantum Cryptography Standard Mandated",
        trend_summary="Governments mandate immediate post-quantum algorithm migration.",
        llm=None,
    )
    for sc in scenes:
        assert sc.visual.camera_motion in ["static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "ken_burns"]
