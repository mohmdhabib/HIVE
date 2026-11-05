from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

PlatformType = Literal["instagram", "youtube", "facebook", "twitter", "manual"]
PublicationStatus = Literal["draft", "scheduled", "publishing", "published", "failed", "manual_required"]

class AccountConnection(BaseModel):
    """Authorized social platform connection for a worker brand."""
    id: str
    worker_id: str
    platform: PlatformType
    account_handle: str
    display_name: str
    status: Literal["connected", "disconnected", "unauthorized", "manual_only"] = "manual_only"
    permissions: list[str] = Field(default_factory=list)
    token_expiry: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScheduledPublication(BaseModel):
    """Scheduled or published content record."""
    id: str
    worker_id: str
    task_id: str
    platform: PlatformType
    status: PublicationStatus = "draft"
    scheduled_at: datetime
    published_at: datetime | None = None
    platform_post_id: str | None = None
    platform_url: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    manual_instructions: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PostAnalytics(BaseModel):
    """Verified platform performance metrics."""
    platform_post_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    estimated_revenue: float = 0.0
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

