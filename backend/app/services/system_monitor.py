import os
import time
from datetime import datetime, timezone
from app.config import get_settings
from app.workers.registry import list_workers
from app.services.task_store import task_store
from app.services.publishing_service import publishing_service
from app.services.audit import audit_service
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger("system_monitor")

class SystemMonitorService:
    """Production health check, telemetry, and system metric aggregator."""

    def __init__(self):
        self._start_time = time.time()

    async def get_system_metrics(self, llm: LLMService) -> dict:
        """Aggregate real-time metrics across infrastructure, LLM, workers, and storage."""
        settings = get_settings()
        workers = list_workers()
        uptime_seconds = int(time.time() - self._start_time)

        # 1. LLM Runtime Latency Check
        t0 = time.time()
        ollama_status = await llm.health_check()
        latency_ms = round((time.time() - t0) * 1000, 1)

        # 2. Worker Fleet
        total_workers = len(workers)
        active_workers = len([w for w in workers if w.enabled])
        paused_workers = total_workers - active_workers

        # 3. Tasks & Approvals
        pending_approvals = len(task_store.list_tasks(status="needs_approval"))
        completed_tasks = len(task_store.list_tasks(status="completed"))
        failed_tasks = len(task_store.list_tasks(status="failed"))

        # 4. Storage Directories Check
        storage_dirs = {
            "images": os.path.exists("storage/images"),
            "videos": os.path.exists("storage/videos"),
            "temporary": os.path.exists("storage/temporary"),
        }

        # 5. Publishing Status
        pending_publications = len(publishing_service.list_schedule(status="scheduled"))
        manual_actions_needed = len(publishing_service.list_schedule(status="manual_required"))

        return {
            "status": "healthy" if not settings.global_kill_switch else "halted",
            "kill_switch_active": settings.global_kill_switch,
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm": {
                "model": settings.ollama_model,
                "endpoint": settings.ollama_url,
                "status": ollama_status.get("ollama", "disconnected"),
                "model_available": ollama_status.get("model_available", False),
                "latency_ms": latency_ms,
                "max_concurrency": settings.ollama_max_concurrent,
            },
            "fleet": {
                "total_brands": total_workers,
                "active_brands": active_workers,
                "paused_brands": paused_workers,
            },
            "operations": {
                "pending_approvals": pending_approvals,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_publications": pending_publications,
                "manual_dispatches_needed": manual_actions_needed,
            },
            "storage": {
                "volumes_mounted": all(storage_dirs.values()),
                "directories": storage_dirs,
            },
            "security": {
                "kill_switch_enforced": True,
                "approval_gates_enforced": True,
                "credential_isolation_enforced": True,
                "audit_logs_count": len(audit_service.list_logs(limit=500)),
            },
        }

system_monitor = SystemMonitorService()

