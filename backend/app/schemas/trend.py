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

