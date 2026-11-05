from typing import List, Optional, Literal
from pydantic import BaseModel, Field

PerformanceSignal = Literal["viral", "high_performing", "average", "underperforming", "hook_fatigue"]

class WorkerPerformanceDigest(BaseModel):
    worker_id: str
    worker_name: str
    niche: str
    yesterday_reach: int = Field(default=0, description="Impressions/views in last 24h")
    avg_3s_retention_pct: float = Field(default=0.0, description="3-second hook hold rate (0-100%)")
    top_performing_hook: Optional[str] = None
    top_performing_archetype: str = "contrarian"
    status_signal: PerformanceSignal = "average"
    diagnosis: str = Field(..., description="Master Agent's analytical diagnosis of why it succeeded or failed")
    recommended_pivot: str = Field(..., description="Actionable strategy directive for today")
    proposed_topic: str = Field(..., description="Today's assigned topic")
    proposed_daily_hook: str = Field(..., description="Hook formula to test today")
    virality_probability: int = Field(default=75, ge=1, le=100)

class MasterExecutiveBriefing(BaseModel):
    briefing_id: str
    date: str
    headline: str
    executive_summary: str = Field(..., description="Direct message from Master Agent to Operator")
    network_reach_24h: int
    network_retention_avg_pct: float
    viral_winners: List[WorkerPerformanceDigest]
    underperformers: List[WorkerPerformanceDigest]
    worker_directives: List[WorkerPerformanceDigest]
    system_recommendation: str
    status: Literal["pending_review", "approved", "executing"] = "pending_review"

