from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

class AuditLogEntry(BaseModel):
    id: str = Field(default="")
    actor: str = "operator"
    action: str  # e.g., 'task.created', 'task.approved', 'task.rejected', 'worker.paused', 'kill_switch.engaged'
    resource_type: str  # e.g., 'task', 'worker', 'system'
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

