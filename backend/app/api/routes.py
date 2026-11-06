from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from app.schemas.task import TaskRequest, TaskReport, TaskPlan
from app.schemas.worker import WorkerConfig
from app.schemas.memory import MemoryEntry
from app.schemas.audit import AuditLogEntry
from app.schemas.content import TopicOpportunity, MultiFormatDeliverable
from app.schemas.platform import PlatformType, AccountConnection, ScheduledPublication
from app.schemas.revenue import RevenueEvent, CostEvent, WorkerProfitability, FinancialSummary, RevenueStream, AttributionType, CostType
from app.schemas.trend import LiveTrendItem, TrendAnalysisRequest, NicheTrendDigest
from app.schemas.video import (
    VideoProductionBlueprint,
    ViralityScorecard,
    RenderJobStatus,
    SceneClipArtifact,
    SceneUpdateRequest,
)
from app.schemas.briefing import MasterExecutiveBriefing, WorkerPerformanceDigest
from app.workers.registry import list_workers, get_worker
from app.master.agent import delegate
from app.master.strategy import prioritize_task
from app.services.llm import LLMService
from app.services.task_store import task_store
from app.services.memory import memory_service
from app.services.audit import audit_service
from app.services.content_pipeline import content_pipeline
from app.services.publishing_service import publishing_service
from app.services.revenue_service import revenue_service
from app.services.system_monitor import system_monitor
from app.services.trend_research import trend_research_service
from app.services.video_engine import video_engine
from app.services.video_renderer import video_renderer
from app.services.master_briefing import master_briefing_service
from app.dependencies import get_llm_service
from app.config import Settings, get_settings
from app.core.exceptions import WorkerNotFoundError, WorkerDisabledError, KillSwitchActiveError, LLMError
from app.core.logging import get_logger

logger = get_logger("api")
router = APIRouter(prefix="/api")

# ============================================================================
# SYSTEM & HEALTH (MILESTONE 1 & 7)
# ============================================================================
@router.get("/health")
async def health(llm: LLMService = Depends(get_llm_service)):
    llm_status = await llm.health_check()
    return {
        "status": "ok",
        "service": "hive-api",
        "ollama": llm_status,
    }

@router.get("/system/metrics")
async def system_metrics_endpoint(llm: LLMService = Depends(get_llm_service)):
    return await system_monitor.get_system_metrics(llm)

class KillSwitchToggleRequest(BaseModel):
    active: bool
    reason: str = "Operator manual toggle"

@router.post("/system/kill-switch")
async def toggle_kill_switch(req: KillSwitchToggleRequest, settings: Settings = Depends(get_settings)):
    settings.global_kill_switch = req.active
    audit_service.record(
        action="kill_switch.toggled",
        resource_type="system",
        resource_id="global",
        details={"active": req.active, "reason": req.reason}
    )
    return {
        "status": "updated",
        "kill_switch_active": settings.global_kill_switch,
        "message": "EMERGENCY KILL SWITCH ENGAGED - ALL AUTONOMOUS ACTIONS FROZEN" if req.active else "Kill switch disengaged - Normal operations resumed"
    }

@router.get("/master/status")
async def master_status(settings: Settings = Depends(get_settings)):
    workers = list_workers()
    pending_tasks = task_store.list_tasks(status="needs_approval")
    return {
        "status": "active" if not settings.global_kill_switch else "halted",
        "kill_switch_active": settings.global_kill_switch,
        "worker_count": len(workers),
        "workers_enabled": len([w for w in workers if w.enabled]),
        "pending_approvals_count": len(pending_tasks),
        "model": settings.ollama_model,
        "max_concurrent": settings.ollama_max_concurrent,
    }

@router.post("/master/prioritize", response_model=TaskPlan)
async def prioritize(request: TaskRequest):
    return prioritize_task(request)

@router.get("/master/briefing", response_model=MasterExecutiveBriefing)
async def get_master_briefing():
    return master_briefing_service.get_latest_briefing()

@router.post("/master/briefing/generate", response_model=MasterExecutiveBriefing)
async def generate_master_briefing(llm: LLMService = Depends(get_llm_service)):
    return await master_briefing_service.generate_fresh_briefing(llm=llm)

@router.post("/master/briefing/approve", response_model=MasterExecutiveBriefing)
async def approve_master_directives():
    return master_briefing_service.approve_and_dispatch()

# ============================================================================
# WORKERS MANAGEMENT
# ============================================================================
@router.get("/workers", response_model=list[WorkerConfig])
async def workers():
    return list_workers()

@router.get("/workers/{worker_id}", response_model=WorkerConfig)
async def worker_detail(worker_id: str):
    try:
        return get_worker(worker_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")

@router.post("/workers/{worker_id}/pause", response_model=WorkerConfig)
async def pause_worker(worker_id: str):
    try:
        worker = get_worker(worker_id)
        worker.enabled = False
        worker.status = "paused"
        audit_service.record("worker.paused", "worker", worker_id)
        return worker
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")

@router.post("/workers/{worker_id}/resume", response_model=WorkerConfig)
async def resume_worker(worker_id: str):
    try:
        worker = get_worker(worker_id)
        worker.enabled = True
        worker.status = "idle"
        audit_service.record("worker.resumed", "worker", worker_id)
        return worker
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")

@router.get("/workers/{worker_id}/memory", response_model=list[MemoryEntry])
async def worker_memory(worker_id: str, category: str | None = None, limit: int = 20):
    try:
        get_worker(worker_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")
    return memory_service.get_entries(worker_id=worker_id, category=category, limit=limit)

# ============================================================================
# REVENUE & PROFITABILITY ENGINE (MILESTONE 6)
# ============================================================================
class RecordRevenueRequest(BaseModel):
    worker_id: str
    platform: str
    stream: RevenueStream
    gross_amount: float
    attribution_type: AttributionType = "measured"
    campaign_id: str | None = None
    task_id: str | None = None
    conversion_metadata: dict | None = None

class RecordCostRequest(BaseModel):
    cost_type: CostType
    amount: float
    description: str
    worker_id: str | None = None
    task_id: str | None = None

@router.get("/revenue/summary", response_model=FinancialSummary)
async def financial_summary():
    return revenue_service.get_financial_summary()

@router.get("/revenue/workers/{worker_id}", response_model=WorkerProfitability)
async def worker_profitability(worker_id: str):
    try:
        return revenue_service.calculate_worker_profitability(worker_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")

@router.post("/revenue/events", response_model=RevenueEvent)
async def record_revenue_endpoint(req: RecordRevenueRequest):
    try:
        return revenue_service.record_revenue(
            worker_id=req.worker_id,
            platform=req.platform,
            stream=req.stream,
            gross_amount=req.gross_amount,
            attribution_type=req.attribution_type,
            campaign_id=req.campaign_id,
            task_id=req.task_id,
            conversion_metadata=req.conversion_metadata,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.post("/revenue/costs", response_model=CostEvent)
async def record_cost_endpoint(req: RecordCostRequest):
    return revenue_service.record_cost(
        cost_type=req.cost_type,
        amount=req.amount,
        description=req.description,
        worker_id=req.worker_id,
        task_id=req.task_id,
    )

# ============================================================================
# VIDEO INTELLIGENCE ENGINE
# ============================================================================
class VideoBlueprintRequest(BaseModel):
    worker_id: str
    trend_title: str
    trend_summary: str | None = None
    source_trend_id: str | None = None

@router.post("/video/blueprint", response_model=VideoProductionBlueprint)
async def generate_video_blueprint(
    req: VideoBlueprintRequest,
    llm: LLMService = Depends(get_llm_service),
):
    try:
        return await video_engine.generate_blueprint_from_trend(
            worker_id=req.worker_id,
            trend_title=req.trend_title,
            trend_summary=req.trend_summary,
            source_trend_id=req.source_trend_id,
            llm=llm,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{req.worker_id}' not found")
    except Exception as exc:
        logger.exception("Error generating video blueprint")
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/video/render", response_model=RenderJobStatus)
async def render_video_endpoint(blueprint: VideoProductionBlueprint):
    try:
        return video_renderer.start_background_render(blueprint)
    except Exception as exc:
        logger.exception("Error initiating video render")
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/video/render/{job_id}", response_model=RenderJobStatus)
async def get_render_status(job_id: str):
    job = video_renderer.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    return job

@router.get("/video/library")
async def list_video_library():
    return video_renderer.list_rendered_videos()

@router.get("/video/blueprint/{blueprint_id}/clips", response_model=list[SceneClipArtifact])
async def get_blueprint_scene_clips(blueprint_id: str):
    return video_renderer.get_scene_clips(blueprint_id)

@router.post("/video/blueprint/{blueprint_id}/scene/{scene_idx}/render", response_model=RenderJobStatus)
async def regenerate_single_scene_endpoint(
    blueprint_id: str,
    scene_idx: int,
    req: SceneUpdateRequest,
):
    try:
        return video_renderer.render_single_scene(
            blueprint_id=blueprint_id,
            scene_idx=scene_idx,
            update=req,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Error regenerating scene %d for blueprint %s", scene_idx, blueprint_id)
        raise HTTPException(status_code=500, detail=str(exc))

# ============================================================================
# AUTOMATED MEDIA HARVESTER & VAULT
# ============================================================================
from app.services.media_harvester import media_harvester, VaultAsset, HarvestRequest

class HarvestUrlRequest(BaseModel):
    url: str
    niche: str = "tech"
    tags: list[str] | None = None

@router.get("/materials/vault", response_model=list[VaultAsset])
async def list_vault_materials(niche: str | None = None):
    return media_harvester.list_vault_assets(niche=niche)

@router.post("/materials/harvest-url", response_model=list[VaultAsset])
async def harvest_from_url_endpoint(req: HarvestUrlRequest):
    try:
        return media_harvester.harvest_from_url(
            url=req.url,
            niche=req.niche,
            custom_tags=req.tags,
        )
    except Exception as exc:
        logger.exception("Error harvesting from URL")
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/materials/harvest-batch", response_model=list[VaultAsset])
async def harvest_batch_endpoint(req: HarvestRequest):
    try:
        return media_harvester.harvest_stock_batch(
            niche=req.niche,
            count=req.count,
        )
    except Exception as exc:
        logger.exception("Error during batch media harvesting")
        raise HTTPException(status_code=500, detail=str(exc))

# ============================================================================
# LIVE TREND RESEARCH SERVICE
# ============================================================================
@router.get("/trends/live", response_model=list[LiveTrendItem])
async def get_live_trends(worker_id: str = Query("tech"), limit: int = Query(8, ge=1, le=25)):
    try:
        return await trend_research_service.get_live_trends_for_worker(worker_id=worker_id, limit=limit)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")
    except Exception as exc:
        logger.exception("Error fetching live trends")
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/trends/analyze", response_model=NicheTrendDigest)
async def analyze_live_trends(
    req: TrendAnalysisRequest,
    llm: LLMService = Depends(get_llm_service),
):
    try:
        items = await trend_research_service.get_live_trends_for_worker(worker_id=req.worker_id)
        if req.trend_ids:
            items = [item for item in items if item.id in req.trend_ids]
        return await trend_research_service.analyze_trends_with_llm(
            worker_id=req.worker_id,
            trends=items,
            llm=llm,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{req.worker_id}' not found")
    except Exception as exc:
        logger.exception("Error analyzing live trends")
        raise HTTPException(status_code=500, detail=str(exc))

# ============================================================================
# CONTENT PRODUCTION STUDIO (MILESTONE 4)
# ============================================================================
class ResearchRequest(BaseModel):
    worker_id: str
    keyword: str | None = None

class MultiFormatRequest(BaseModel):
    worker_id: str
    topic: TopicOpportunity

@router.post("/content/research", response_model=list[TopicOpportunity])
async def research_topics_endpoint(
    req: ResearchRequest,
    llm: LLMService = Depends(get_llm_service),
):
    try:
        return await content_pipeline.research_topics(
            worker_id=req.worker_id,
            llm=llm,
            keyword=req.keyword,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{req.worker_id}' not found")
    except Exception as exc:
        logger.exception("Error during topic research")
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/content/generate-multi-format", response_model=MultiFormatDeliverable)
async def generate_multi_format_endpoint(
    req: MultiFormatRequest,
    llm: LLMService = Depends(get_llm_service),
):
    try:
        return await content_pipeline.generate_multi_format_package(
            worker_id=req.worker_id,
            topic=req.topic,
            llm=llm,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{req.worker_id}' not found")
    except Exception as exc:
        logger.exception("Error during multi-format generation")
        raise HTTPException(status_code=500, detail=str(exc))

# ============================================================================
# SOCIAL MEDIA & PUBLISHING (MILESTONE 5)
# ============================================================================
class ScheduleRequest(BaseModel):
    task_id: str
    platform: PlatformType
    scheduled_at: datetime

class ManualCompleteRequest(BaseModel):
    platform_url: str

@router.get("/integrations/accounts", response_model=list[AccountConnection])
async def list_connected_accounts(worker_id: str | None = None):
    return publishing_service.list_accounts(worker_id=worker_id)

@router.get("/publishing/schedule", response_model=list[ScheduledPublication])
async def list_publishing_schedule(worker_id: str | None = None, status: str | None = None):
    return publishing_service.list_schedule(worker_id=worker_id, status=status)

@router.post("/publishing/schedule", response_model=ScheduledPublication)
async def schedule_publication_endpoint(req: ScheduleRequest):
    try:
        return publishing_service.schedule_publication(
            task_id=req.task_id,
            platform=req.platform,
            scheduled_at=req.scheduled_at,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/publishing/{schedule_id}/publish-now", response_model=ScheduledPublication)
async def publish_now_endpoint(schedule_id: str):
    try:
        return await publishing_service.publish_now(schedule_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Publication '{schedule_id}' not found")

@router.post("/publishing/{schedule_id}/complete-manual", response_model=ScheduledPublication)
async def complete_manual_endpoint(schedule_id: str, req: ManualCompleteRequest):
    try:
        return publishing_service.complete_manual_publication(schedule_id, req.platform_url)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Publication '{schedule_id}' not found")

# ============================================================================
# TASKS & APPROVAL WORKFLOW
# ============================================================================
@router.get("/tasks", response_model=list[TaskReport])
async def list_tasks(
    worker_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    return task_store.list_tasks(worker_id=worker_id, status=status, limit=limit)

@router.get("/tasks/{task_id}", response_model=TaskReport)
async def get_task(task_id: str):
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task

@router.post("/tasks/{task_id}/approve", response_model=TaskReport)
async def approve_task(task_id: str):
    try:
        approved = task_store.approve_task(task_id)
        audit_service.record("task.approved", "task", task_id, details={"status": approved.status})
        return approved
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

@router.post("/tasks/{task_id}/reject", response_model=TaskReport)
async def reject_task(task_id: str, reason: str = "Operator rejected"):
    try:
        rejected = task_store.reject_task(task_id, reason=reason)
        audit_service.record("task.rejected", "task", task_id, details={"reason": reason})
        return rejected
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

@router.post("/tasks", response_model=TaskReport)
async def create_task(
    request: TaskRequest,
    llm: LLMService = Depends(get_llm_service),
):
    try:
        return await delegate(request, llm)
    except KeyError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except WorkerDisabledError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KillSwitchActiveError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM service error: {exc}")
    except Exception as exc:
        logger.exception("Unexpected error in create_task")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

# ============================================================================
# AUDIT LOGS
# ============================================================================
@router.get("/audit-logs", response_model=list[AuditLogEntry])
async def list_audit_logs(limit: int = 50, resource_type: str | None = None):
    return audit_service.list_logs(limit=limit, resource_type=resource_type)
