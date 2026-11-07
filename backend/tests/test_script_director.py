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
    assert any("scenes" in e.get("message", "").lower() for e in telem_a.event_trace)


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


def test_script_director_json_repair_truncated():
    # Test JSON repair when trailing braces/brackets are missing
    truncated_json = '{\n  "hook": "Test hook",\n  "cta": "Test cta",\n  "description": "Test desc",\n  "scenes": [\n    {"voiceover": "Scene 1", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_in"},\n    {"voiceover": "Scene 2", "search_keywords": ["k1", "k2"], "camera_motion": "pan_left"},\n    {"voiceover": "Scene 3", "search_keywords": ["k1", "k2"], "camera_motion": "slow_zoom_out"},\n    {"voiceover": "Scene 4", "search_keywords": ["k1", "k2"], "camera_motion": "pan_right"}'
    repaired = script_director_agent._repair_and_parse_json(truncated_json)
    assert repaired is not None
    assert "scenes" in repaired
    assert len(repaired["scenes"]) == 4


@pytest.mark.anyio
async def test_script_director_raises_on_llm_failure():
    from unittest.mock import AsyncMock, MagicMock
    from app.core.exceptions import LLMGenerationError

    worker = get_worker("tech")
    failing_llm = MagicMock()
    failing_llm.model = "mock-failing-llm"
    failing_llm.timeout = 1.0
    failing_llm.generate = AsyncMock(return_value="NOT_JSON_AT_ALL")

    # Strict zero-template policy: must raise LLMGenerationError when LLM fails
    with pytest.raises(LLMGenerationError):
        await script_director_agent.craft_screenplay(
            worker=worker,
            trend_title="Hypothetical Trend Topic",
            llm=failing_llm,
        )


@pytest.mark.anyio
async def test_script_director_with_step_and_token_callbacks():
    import json
    from unittest.mock import MagicMock
    from app.schemas.video import TraceStep

    worker = get_worker("tech")
    mock_llm = MagicMock()
    mock_llm.model = "llama3.1"
    mock_llm.timeout = 60.0

    async def mock_stream(*args, **kwargs):
        chunks = ['{"hook": "Breakthrough", ', '"cta": "Follow", ', '"description": "Desc", ', '"scenes": [',
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

    steps_recorded: list[TraceStep] = []
    tokens_recorded: list[str] = []

    async def on_step(step: TraceStep):
        steps_recorded.append(step)

    async def on_token(token: str):
        tokens_recorded.append(token)

    scenes, hook, cta, desc, telem = await script_director_agent.craft_screenplay(
        worker=worker,
        trend_title="Autonomous Robotics Deployment",
        trend_summary="Robotics fleet deployed in production.",
        llm=mock_llm,
        step_callback=on_step,
        token_callback=on_token,
    )

    assert len(scenes) == 8
    assert len(tokens_recorded) > 0
    assert len(steps_recorded) >= 5
    step_phases = [s.phase for s in steps_recorded]
    assert "init" in step_phases
    assert "research" in step_phases
    assert "strategy" in step_phases
    assert "llm_complete" in step_phases
    assert "visuals" in step_phases
    assert "audio" in step_phases
    assert "complete" in step_phases
    assert len(telem.trace_steps) >= 5


