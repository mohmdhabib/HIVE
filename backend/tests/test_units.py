from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.config import Settings, get_settings
from app.workers.registry import list_workers, get_worker
from app.schemas.worker import WorkerConfig, WorkerRevenueTarget
from app.schemas.task import TaskRequest, TaskReport, TaskPlan
from app.schemas.content import (
    ContentPiece,
    QualityCheckResult,
    TopicOpportunity,
    SlideItem,
    ThreadPost,
    CreativeAssetBrief,
    MultiFormatDeliverable,
)
from app.schemas.platform import AccountConnection, ScheduledPublication
from app.schemas.revenue import RevenueEvent, CostEvent, WorkerProfitability, FinancialSummary
from app.schemas.memory import MemoryEntry, WorkerMemoryContext
from app.core.exceptions import (
    HiveError,
    WorkerNotFoundError,
    WorkerDisabledError,
    KillSwitchActiveError,
    LLMError,
    LLMTimeoutError,
)
from app.services.llm import LLMService
from app.services.memory import WorkerMemoryService
from app.services.task_store import TaskStoreService, task_store
from app.services.audit import AuditLogService
from app.services.content_pipeline import ContentPipelineService
from app.services.publishing_service import PublishingService
from app.services.revenue_service import RevenueService, revenue_service
from app.services.system_monitor import SystemMonitorService
from app.integrations.manual import ManualPublishingAdapter
from app.integrations.instagram import InstagramAdapter
from app.integrations.youtube import YouTubeAdapter
from app.master.strategy import prioritize_task
from app.master.evaluator import evaluate_execution
from app.master.agent import master_graph
from app.workers.pipeline import worker_pipeline_graph

def test_settings_defaults():
    settings = get_settings()
    assert settings.app_name == "HIVE Agent Network"
    assert settings.app_version == "0.1.0"
    assert settings.ollama_model == "llama3.1"
    assert settings.ollama_timeout == 180.0
    assert settings.ollama_max_concurrent == 2
    assert settings.global_kill_switch is False

def test_workers_registry_pillars_and_targets():
    workers = list_workers()
    assert len(workers) == 5
    for w in workers:
        assert len(w.content_pillars) >= 3
        assert w.revenue_target.monthly_target_usd > 0
        assert w.revenue_target.target_rpm > 0

def test_get_worker_valid():
    worker = get_worker("tech")
    assert worker.id == "tech"
    assert worker.name == "Signal Tech"
    assert worker.enabled is True
    assert "LLM breakthroughs" in worker.content_pillars

def test_get_worker_invalid():
    with pytest.raises(KeyError):
        get_worker("unknown_worker")

def test_prioritize_task_urgent():
    req = TaskRequest(
        worker_id="tech",
        objective="Breaking news: major AI vulnerability reported immediately",
        target_platform="x"
    )
    plan = prioritize_task(req)
    assert plan.priority == "critical"
    assert plan.estimated_tokens <= 1000

def test_prioritize_task_revenue():
    req = TaskRequest(
        worker_id="business",
        objective="Outline new affiliate campaign sponsorship package",
        target_platform="youtube_shorts"
    )
    plan = prioritize_task(req)
    assert plan.priority == "high"
    assert plan.estimated_tokens >= 2000

def test_content_piece_schema_valid():
    piece = ContentPiece(
        title="3 AI Tools You Cannot Ignore",
        hook="Stop coding the old way in 2026.",
        body_script="Here are 3 agentic frameworks redefining software...",
        caption="Which AI tool is in your daily stack? Link in bio.",
        hashtags=["ai", "coding", "software"],
        visual_brief="Screen recording showing terminal + split camera.",
        target_platform="instagram",
        monetization_hypothesis="Affiliate commissions via bio link for tool #1.",
        factual_checks=["Verify benchmark claims from paper."],
        estimated_risk_level="low",
        risks_and_caveats=["Ensure tool #1 pricing is updated."]
    )
    assert piece.title == "3 AI Tools You Cannot Ignore"
    assert piece.estimated_risk_level == "low"
    assert len(piece.hashtags) == 3

def test_evaluator_forces_approval_on_high_risk():
    piece = ContentPiece(
        title="Controversial Financial Breakdown",
        hook="Why this startup was a fraud.",
        body_script="Detailed teardown...",
        caption="Unpacking the metrics.",
        visual_brief="Charts and slides.",
        target_platform="x",
        monetization_hypothesis="Sponsorship slot.",
        factual_checks=["Check SEC filing", "Verify revenue numbers", "Check CEO statement"],
        estimated_risk_level="high",
        risks_and_caveats=["Defamation risk if numbers are inaccurate."]
    )
    report = TaskReport(
        task_id="eval-1",
        worker_id="business",
        worker_name="Founder Brief",
        objective="Teardown startup failure",
        status="completed",
        content=piece,
        approval_required=False,
    )
    evaluated = evaluate_execution(report)
    assert evaluated.approval_required is True
    assert evaluated.status == "needs_approval"

def test_master_graph_nodes():
    nodes = list(master_graph.nodes.keys())
    assert "check_kill_switch" in nodes
    assert "prioritize_and_plan" in nodes
    assert "validate_assignment" in nodes
    assert "delegate_to_worker" in nodes
    assert "evaluate_report" in nodes

def test_worker_pipeline_graph_nodes():
    nodes = list(worker_pipeline_graph.nodes.keys())
    assert "research_and_angle" in nodes
    assert "generate_content_piece" in nodes
    assert "quality_and_factuality_check" in nodes
    assert "compile_task_report" in nodes

def test_llm_json_parsing_helper():
    settings = Settings()
    service = LLMService(settings)
    raw_json = '{"title":"Test","hook":"Hook text here","body_script":"Body","caption":"Cap","hashtags":[],"visual_brief":"Visuals","target_platform":"instagram","monetization_hypothesis":"Monetize via bio link","factual_checks":[],"estimated_risk_level":"low","risks_and_caveats":[]}'
    parsed = service._parse_json_to_schema(raw_json, ContentPiece)
    assert parsed.title == "Test"
    assert parsed.target_platform == "instagram"

def test_worker_memory_isolation():
    mem = WorkerMemoryService()
    mem.add_entry("tech", "topic_history", "Topic A", {"title": "Tech Topic A"})
    mem.add_entry("business", "topic_history", "Topic B", {"title": "Biz Topic B"})

    tech_entries = mem.get_entries("tech")
    biz_entries = mem.get_entries("business")

    assert len(tech_entries) == 1
    assert len(biz_entries) == 1
    assert tech_entries[0].key == "Topic A"
    assert biz_entries[0].key == "Topic B"

def test_worker_memory_context_compilation():
    mem = WorkerMemoryService()
    mem.add_entry("tech", "topic_history", "LLM Benchmarks", {"title": "LLM Benchmarks"})
    mem.add_entry("tech", "successful_pattern", "3s visual pattern interrupt", {"pattern": "3s visual pattern interrupt"})

    ctx = mem.get_worker_context("tech")
    assert "LLM Benchmarks" in ctx.recent_topics
    assert "3s visual pattern interrupt" in ctx.successful_patterns

def test_cross_worker_learning_without_leakage():
    mem = WorkerMemoryService()
    mem.add_entry("tech", "successful_pattern", "Fast text overlay pacing", {"pattern": "Fast text overlay pacing"})
    mem.add_entry("entertainment", "successful_pattern", "Cliffhanger question hook", {"pattern": "Cliffhanger question hook"})

    insights_for_business = mem.get_cross_worker_insights(exclude_worker_id="business")
    assert len(insights_for_business) == 2
    assert "Fast text overlay pacing" in insights_for_business
    assert "Cliffhanger question hook" in insights_for_business

    insights_for_tech = mem.get_cross_worker_insights(exclude_worker_id="tech")
    assert "Fast text overlay pacing" not in insights_for_tech

def test_task_store_lifecycle_and_approval():
    store = TaskStoreService()
    report = TaskReport(
        task_id="task-999",
        worker_id="tech",
        worker_name="Signal Tech",
        objective="Generate benchmark script",
        status="needs_approval",
        approval_required=True,
    )
    store.save_task(report)
    retrieved = store.get_task("task-999")
    assert retrieved is not None
    assert retrieved.status == "needs_approval"

    approved = store.approve_task("task-999")
    assert approved.status == "completed"
    assert approved.approval_required is False

def test_task_store_rejection():
    store = TaskStoreService()
    report = TaskReport(
        task_id="task-888",
        worker_id="education",
        worker_name="Curiosity Daily",
        objective="Draft historical event timeline",
        status="needs_approval",
        approval_required=True,
        quality_check=QualityCheckResult(passed=True, score=0.85, feedback=[])
    )
    store.save_task(report)
    rejected = store.reject_task("task-888", reason="Need more primary sources")
    assert rejected.status == "failed"
    assert any("Need more primary sources" in f for f in rejected.quality_check.feedback)

def test_audit_log_service():
    audit = AuditLogService()
    audit.record("task.created", "task", "task-001", details={"worker": "tech"})
    audit.record("task.approved", "task", "task-001", details={"operator": "MH"})

    logs = audit.list_logs()
    assert len(logs) == 2
    assert logs[0].action == "task.approved"
    assert logs[1].action == "task.created"

def test_topic_opportunity_schema():
    topic = TopicOpportunity(
        title="5 Autonomous Agent Frameworks Tested",
        hook_angle="Most developer benchmarks are fundamentally flawed.",
        timeliness_factor="Q1 agent framework release cycle.",
        target_audience_segment="Senior engineers & AI builders",
        estimated_reach_potential="viral",
        monetization_angle="Affiliate link to cloud compute provider."
    )
    assert topic.title == "5 Autonomous Agent Frameworks Tested"
    assert topic.estimated_reach_potential == "viral"

def test_slide_item_and_thread_post():
    slide = SlideItem(
        slide_number=1,
        headline="The Agentic Shift",
        body_text="Why single-prompt LLMs are being replaced by state machines.",
        visual_direction="Dark aesthetic diagram"
    )
    assert slide.slide_number == 1

    post = ThreadPost(
        post_number=1,
        text="1/ The way we build AI software just changed permanently. Here is why: 🧵",
        suggested_media="Header chart"
    )
    assert post.post_number == 1
    assert len(post.text) <= 280

def test_creative_asset_brief():
    brief = CreativeAssetBrief(
        asset_type="thumbnail",
        prompt="Cinematic dark-mode tech workspace with amber backlight, high resolution",
        aspect_ratio="1:1",
        overlay_text="AGENT ARCHITECTURE 2026",
        color_palette=["#090b10", "#f5a623"]
    )
    assert brief.aspect_ratio == "1:1"
    assert brief.asset_type == "thumbnail"

def test_content_pipeline_fallback_generation():
    worker = get_worker("tech")
    pipeline = ContentPipelineService()
    topics = pipeline._fallback_topics(worker)
    assert len(topics) >= 3

    pkg = pipeline._fallback_package(worker, topics[0])
    assert pkg.short_video is not None
    assert len(pkg.thread_posts) >= 3
    assert len(pkg.carousel_slides) >= 3
    assert len(pkg.creative_assets) == 2

def test_manual_publishing_adapter():
    adapter = ManualPublishingAdapter()
    piece = ContentPiece(
        title="AI Agent Security",
        hook="Your agents are leaking context.",
        body_script="Script here...",
        caption="Review your agent boundary checks.",
        hashtags=["security", "ai"],
        visual_brief="Dark terminal with red alerts.",
        target_platform="instagram",
        monetization_hypothesis="Security audit lead gen.",
    )
    instructions = adapter.get_manual_instructions(piece)
    assert "MANUAL PUBLISHING DISPATCH" in instructions
    assert piece.hook in instructions
    assert piece.caption in instructions

def test_instagram_adapter_eligibility():
    adapter = InstagramAdapter()
    unauth_acc = AccountConnection(
        id="acc-1", worker_id="tech", platform="instagram",
        account_handle="@signaltech", display_name="Signal Tech",
        status="disconnected", permissions=[]
    )
    res = adapter.check_eligibility(unauth_acc)
    assert res["eligible"] is False
    assert "instagram_content_publish" in res["missing_permissions"]

def test_publishing_service_blocks_unapproved_content():
    pub_service = PublishingService()
    store = task_store
    unapproved_task = TaskReport(
        task_id="unapproved-001",
        worker_id="tech",
        worker_name="Signal Tech",
        objective="Test draft scheduling",
        status="needs_approval",
        approval_required=True,
        content=ContentPiece(
            title="Draft", hook="Hook", body_script="Body", caption="Cap",
            visual_brief="Visual", monetization_hypothesis="Hypothesis"
        )
    )
    store.save_task(unapproved_task)

    with pytest.raises(ValueError) as excinfo:
        pub_service.schedule_publication(
            task_id="unapproved-001",
            platform="instagram",
            scheduled_at=datetime.now(timezone.utc)
        )
    assert "requires human operator approval" in str(excinfo.value)

def test_publishing_service_schedules_approved_content():
    pub_service = PublishingService()
    store = task_store
    approved_task = TaskReport(
        task_id="approved-001",
        worker_id="tech",
        worker_name="Signal Tech",
        objective="Test approved scheduling",
        status="completed",
        approval_required=False,
        content=ContentPiece(
            title="Approved Post", hook="Hook", body_script="Body", caption="Cap",
            visual_brief="Visual", monetization_hypothesis="Hypothesis"
        )
    )
    store.save_task(approved_task)

    sched = pub_service.schedule_publication(
        task_id="approved-001",
        platform="manual",
        scheduled_at=datetime.now(timezone.utc)
    )
    assert sched.status == "scheduled"
    assert sched.task_id == "approved-001"

# ============================================================================
# MILESTONE 6 TESTS: REVENUE & FINANCIAL ATTRIBUTION
# ============================================================================
def test_revenue_service_financial_summary():
    service = RevenueService()
    summary = service.get_financial_summary()
    assert summary.total_gross_revenue > 0
    assert summary.total_costs > 0
    assert summary.net_profit == round(summary.total_gross_revenue - summary.total_costs, 2)
    assert summary.profit_margin_pct > 0
    assert "affiliate" in summary.stream_breakdown
    assert "sponsorship" in summary.stream_breakdown
    assert len(summary.worker_rankings) == 5

def test_worker_profitability_calculation():
    service = RevenueService()
    prof = service.calculate_worker_profitability("tech")
    assert prof.worker_id == "tech"
    assert prof.gross_revenue > 0
    assert prof.net_profit > 0
    assert prof.profit_margin_pct > 50.0  # high margin digital media network
    assert prof.measured_revenue > 0

def test_record_new_revenue_and_cost():
    service = RevenueService()
    rev = service.record_revenue(
        worker_id="business",
        platform="x",
        stream="sponsorship",
        gross_amount=500.0,
        attribution_type="measured",
        conversion_metadata={"sponsor": "Test Sponsor"}
    )
    assert rev.gross_amount == 500.0

    cost = service.record_cost(
        cost_type="llm_compute",
        amount=5.0,
        description="Local GPU inference test",
        worker_id="business"
    )
    assert cost.amount == 5.0

# ============================================================================
# MILESTONE 7 TESTS: PRODUCTION HARDENING & SYSTEM TELEMETRY
# ============================================================================
def test_system_monitor_structure():
    monitor = SystemMonitorService()
    assert monitor._start_time > 0

def test_kill_switch_blocks_execution_state():
    settings = get_settings()
    settings.global_kill_switch = True
    assert settings.global_kill_switch is True
    # Reset for other tests
    settings.global_kill_switch = False

def test_exceptions_hierarchy():
    assert issubclass(WorkerNotFoundError, HiveError)
    assert issubclass(WorkerDisabledError, HiveError)
    assert issubclass(KillSwitchActiveError, HiveError)
    assert issubclass(LLMError, HiveError)
    assert issubclass(LLMTimeoutError, LLMError)

# ============================================================================
# LIVE TREND RESEARCH TESTS
# ============================================================================
from app.schemas.trend import LiveTrendItem, AnalyzedTrendOpportunity, NicheTrendDigest
from app.services.trend_research import LiveTrendResearchService

def test_live_trend_item_schema():
    item = LiveTrendItem(
        id="hn-12345",
        title="Cursor AI Code Editor adoption surge",
        source="hackernews",
        url="https://news.ycombinator.com/item?id=12345",
        niche="tech",
        score=450,
        comment_count=120,
        summary="Discussion on autonomous AI IDEs."
    )
    assert item.id == "hn-12345"
    assert item.source == "hackernews"
    assert item.score == 450

def test_trend_research_service_fallback_generation():
    service = LiveTrendResearchService()
    test_trends = [
        LiveTrendItem(
            id="t-1",
            title="Local Llama 3.1 8B vs Cloud APIs",
            source="reddit",
            niche="tech",
            score=500,
            comment_count=80
        ),
        LiveTrendItem(
            id="t-2",
            title="Anthropic Computer Use API announcement",
            source="hackernews",
            niche="tech",
            score=900,
            comment_count=300
        )
    ]
    opps = service.generate_fallback_opportunities("tech", test_trends)
    assert len(opps) == 2
    assert opps[0].source_trend_id == "t-1"
    assert "hook_angle" in opps[0].model_dump()
    assert opps[0].virality_score >= 80

def test_trend_digest_structure():
    digest = NicheTrendDigest(
        worker_id="tech",
        niche="AI and technology",
        timestamp="2026-11-05T00:00:00Z",
        total_signals=2,
        trends=[],
        opportunities=[]
    )
    assert digest.worker_id == "tech"
    assert digest.total_signals == 2

# ============================================================================
# VIDEO INTELLIGENCE ENGINE TESTS
# ============================================================================
from app.schemas.video import (
    VideoProductionBlueprint,
    SceneNode,
    VisualDirective,
    AudioDirective,
    EmotionalBeat,
    RetentionZone,
    HookVariant,
)
from app.services.video_engine import (
    video_engine,
    BRAND_IDENTITIES,
    build_scene_graph_template,
    generate_hook_variants,
    score_virality,
)

def test_brand_identities_registry():
    assert "tech" in BRAND_IDENTITIES
    assert "business" in BRAND_IDENTITIES
    assert "entertainment" in BRAND_IDENTITIES
    assert "education" in BRAND_IDENTITIES
    assert "lifestyle" in BRAND_IDENTITIES
    assert BRAND_IDENTITIES["tech"].brand_name == "Signal Tech"
    assert BRAND_IDENTITIES["tech"].colors.primary == "#00d4ff"
    assert BRAND_IDENTITIES["business"].colors.primary == "#f5a623"

def test_build_scene_graph_retention_zones():
    scenes = build_scene_graph_template(
        title="Cursor vs Devin AI Battle",
        hook_text="Stop coding like it is 2023.",
        body_points=["Point 1: Autocomplete speed", "Point 2: Architecture planning"],
        cta_text="Follow for more dev tool teardowns."
    )
    # Must have hook, tension, core, payoff, cta
    assert len(scenes) >= 5
    assert scenes[0].emotional_beat == EmotionalBeat.hook
    assert scenes[0].retention_zone == RetentionZone.critical
    assert scenes[0].duration_seconds <= 3.0
    assert scenes[-1].emotional_beat == EmotionalBeat.cta

def test_generate_hook_variants():
    variants = generate_hook_variants(
        title="Open-Source Local LLMs",
        audience="Developers and AI builders"
    )
    assert len(variants) == 3
    archetypes = {v.hook_archetype for v in variants}
    assert "contrarian" in archetypes
    assert "curiosity_gap" in archetypes
    assert "stat_paradox" in archetypes

def test_video_engine_assemble_blueprint():
    blueprint = video_engine.assemble_blueprint(
        worker_id="tech",
        trend_title="Llama 3.1 405B Outperforms Frontier Models Locally",
        hook_text="Stop coding like it is 2023.",
        body_points=[
            "First benchmark shows 90% parity with cloud models.",
            "Local inference on Mac Studio M2 Ultra runs at 32 tok/s.",
            "Zero cloud token costs makes autonomous loops viable.",
        ],
        cta_text="Follow for more dev tool teardowns.",
        description="Developer community benchmarks show huge local parity.",
        source_trend_id="trend-001",
    )
    assert isinstance(blueprint, VideoProductionBlueprint)
    assert blueprint.worker_id == "tech"
    assert blueprint.brand.brand_name == "Signal Tech"
    assert len(blueprint.scenes) >= 5
    assert blueprint.virality_score is not None
    assert blueprint.virality_score.overall_score > 50
    assert len(blueprint.hook_variants) == 3
    assert blueprint.thumbnail.headline_text != ""

# ============================================================================
# MASTER AGENT EXECUTIVE BRIEFING TESTS
# ============================================================================
from app.schemas.briefing import MasterExecutiveBriefing, WorkerPerformanceDigest
from app.services.master_briefing import MasterBriefingService

def test_master_briefing_structure():
    service = MasterBriefingService()
    briefing = service.get_latest_briefing()
    assert isinstance(briefing, MasterExecutiveBriefing)
    assert briefing.network_reach_24h > 100000
    assert briefing.network_retention_avg_pct > 0.0
    assert len(briefing.worker_directives) == 5
    assert len(briefing.viral_winners) >= 1
    assert any(w.worker_id == "tech" for w in briefing.viral_winners)
    assert any(w.status_signal == "hook_fatigue" for w in briefing.underperformers)
    assert "Good morning, Operator" in briefing.executive_summary

def test_master_briefing_approve_and_dispatch():
    service = MasterBriefingService()
    briefing = service.approve_and_dispatch()
    assert briefing.status == "executing"

# ============================================================================
# VIDEO RENDERING PIPELINE TESTS
# ============================================================================
import os
from app.services.video_renderer import VideoRenderService, get_ffmpeg_binary

def test_video_renderer_initialization_and_binary():
    renderer = VideoRenderService()
    assert os.path.exists(renderer.video_dir)
    assert os.path.exists(renderer.image_dir)
    bin_path = get_ffmpeg_binary()
    assert bin_path != ""

def test_video_renderer_render_blueprint():
    renderer = VideoRenderService()
    bp = video_engine.assemble_blueprint(
        worker_id="tech",
        trend_title="Autonomous Video Pipeline Test",
        hook_text="Stop coding by hand.",
        body_points=["Scene 1: Neural voice active.", "Scene 2: High definition output."],
        cta_text="Follow for more.",
        description="Automated rendering test.",
    )
    job = renderer.render_blueprint(bp)
    assert job.status == "complete"
    assert job.progress_pct == 100.0
    assert job.output_path is not None
    assert job.output_path.endswith(".mp4")
    # Verify the physical video file actually exists on disk!
    disk_path = os.path.join(renderer.video_dir, f"{bp.blueprint_id}.mp4")
    assert os.path.exists(disk_path)
    assert os.path.getsize(disk_path) > 1000





