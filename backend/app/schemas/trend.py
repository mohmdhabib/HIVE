from typing import Optional, List, Literal
from pydantic import BaseModel, Field

TrendSource = Literal["hackernews", "reddit", "google_trends", "rss", "simulated"]
HookArchetype = Literal[
    "contrarian", 
    "curiosity_gap", 
    "urgent_warning", 
    "behind_the_scenes", 
    "stat_paradox",
    "speed_breakdown"
]

class LiveTrendItem(BaseModel):
    id: str
    title: str
    source: TrendSource
    url: Optional[str] = None
    niche: str = Field(..., description="Target niche: tech, biz, culture, facts, lifestyle, or general")
    score: int = Field(default=0, description="Upvotes, points, or traffic indicator")
    comment_count: int = Field(default=0, description="Volume of discussion")
    published_at: Optional[str] = None
    summary: Optional[str] = None

class AnalyzedTrendOpportunity(BaseModel):
    source_trend_id: str
    headline: str
    hook_angle: str = Field(..., description="3-second punchy hook to stop the scroll")
    hook_archetype: HookArchetype = Field(default="curiosity_gap")
    audience_appeal: str = Field(..., description="Why this audience cares right now")
    virality_score: int = Field(default=75, ge=1, le=100)
    monetization_hypothesis: str = Field(..., description="How to convert this attention into revenue")
    suggested_formats: List[str] = Field(default_factory=lambda: ["short_video", "thread", "carousel"])

class TrendAnalysisRequest(BaseModel):
    worker_id: str
    trend_ids: Optional[List[str]] = None
    custom_keywords: Optional[List[str]] = None

class NicheTrendDigest(BaseModel):
    worker_id: str
    niche: str
    timestamp: str
    total_signals: int
    trends: List[LiveTrendItem]
    opportunities: List[AnalyzedTrendOpportunity]


class BatchHarvestRequest(BaseModel):
    worker_ids: Optional[List[str]] = None
    drafts_per_worker: int = Field(default=3, ge=1, le=5)
    min_virality_score: int = Field(default=65, ge=1, le=100)


class HarvestedBlueprintDraft(BaseModel):
    draft_id: str
    worker_id: str
    worker_name: str
    trend_title: str
    source: str
    virality_score: int
    recommendation: str
    hook_preview: str
    blueprint_id: str
    task_id: str
    status: str = "needs_approval"
    scenes_count: int
    duration_seconds: float
    created_at: str


class BatchHarvestReport(BaseModel):
    batch_id: str
    timestamp: str
    total_signals_scanned: int
    total_drafts_generated: int
    workers_covered: List[str]
    drafts: List[HarvestedBlueprintDraft]
    status: str = "completed"
    execution_time_seconds: float


class HarvesterScheduleConfig(BaseModel):
    enabled: bool = True
    cron_expression: str = "0 6 * * *"
    drafts_per_worker: int = 3
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_batch_id: Optional[str] = None
    total_runs: int = 0

