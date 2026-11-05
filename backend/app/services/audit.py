from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.audit import AuditLogEntry
from app.core.logging import get_logger

logger = get_logger("audit")

class AuditLogService:
    """Records security, operational, and lifecycle audit events."""

    def __init__(self):
        self._logs: list[AuditLogEntry] = []

    def record(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor: str = "operator",
        details: dict | None = None,
    ) -> AuditLogEntry:
        """Create an immutable audit log entry."""
        entry = AuditLogEntry(
            id=str(uuid4()),
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            created_at=datetime.now(timezone.utc),
        )
        self._logs.append(entry)
        logger.info(
            "AUDIT LOG: actor=%s action=%s resource=%s:%s",
            actor, action, resource_type, resource_id
        )
        return entry

    def list_logs(self, limit: int = 50, resource_type: str | None = None) -> list[AuditLogEntry]:
        """Fetch audit logs in reverse chronological order."""
        logs = self._logs
        if resource_type:
            logs = [l for l in logs if l.resource_type == resource_type]
        return sorted(logs, key=lambda x: x.created_at, reverse=True)[:limit]

# Global singleton service
audit_service = AuditLogService()

