from datetime import datetime, timezone
from typing import Literal, Any
from pydantic import BaseModel, Field

MemoryCategory = Literal[
    "topic_history",
    "successful_pattern",
    "failed_pattern",
    "audience_performance",
    "strategy_change",
]

class MemoryEntry(BaseModel):
    id: str = Field(default="")
    worker_id: str
    category: MemoryCategory
    key: str
    content: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkerMemoryContext(BaseModel):
    """Context injected into worker prompt during research and drafting."""
    recent_topics: list[str] = Field(default_factory=list)
    successful_patterns: list[str] = Field(default_factory=list)
    banned_or_failed_patterns: list[str] = Field(default_factory=list)
    cross_worker_insights: list[str] = Field(default_factory=list)

