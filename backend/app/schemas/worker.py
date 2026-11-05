from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

WorkerStatus = Literal["idle", "queued", "running", "needs_approval", "completed", "failed", "paused"]

class WorkerRevenueTarget(BaseModel):
    monthly_target_usd: float = 1000.0
    primary_stream: Literal["affiliate", "sponsorships", "leads", "digital_products"] = "affiliate"
    target_rpm: float = 15.0

class WorkerConfig(BaseModel):
    id: str
    name: str
    niche: str
    audience: str
    voice: str
    objective: str
    content_pillars: list[str] = Field(default_factory=list)
    revenue_target: WorkerRevenueTarget = Field(default_factory=WorkerRevenueTarget)
    status: WorkerStatus = "idle"
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

