from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.platform import (
    PlatformType,
    AccountConnection,
    ScheduledPublication,
    PublicationStatus,
)
from app.integrations.base import PlatformAdapter
from app.integrations.manual import ManualPublishingAdapter
from app.integrations.instagram import InstagramAdapter
from app.integrations.youtube import YouTubeAdapter
from app.integrations.twitter import TwitterAdapter
from app.integrations.facebook import FacebookAdapter
from app.services.task_store import task_store
from app.services.audit import audit_service
from app.core.logging import get_logger

logger = get_logger("publishing_service")

class PublishingService:
    """Manages social platform adapters, account connectivity, scheduling, and publication gates."""

    def __init__(self):
        self._adapters: dict[PlatformType, PlatformAdapter] = {
            "manual": ManualPublishingAdapter(),
            "instagram": InstagramAdapter(),
            "youtube": YouTubeAdapter(),
            "twitter": TwitterAdapter(),
            "facebook": FacebookAdapter(),
        }
        self._accounts: dict[str, AccountConnection] = {}
        self._schedule: dict[str, ScheduledPublication] = {}
        self._seed_default_accounts()

    def _seed_default_accounts(self):
        """Seed initial platform account connection records for workers."""
        workers = ["tech", "business", "entertainment", "education", "lifestyle"]
        for wid in workers:
            # Default manual safe fallback
            acc_id = f"acc-{wid}-manual"
            self._accounts[acc_id] = AccountConnection(
                id=acc_id,
                worker_id=wid,
                platform="manual",
                account_handle=f"@{wid}_hive",
                display_name=f"{wid.capitalize()} Network Account",
                status="manual_only",
                permissions=["manual_dispatch_enabled"],
            )

    def get_adapter(self, platform: PlatformType) -> PlatformAdapter:
        return self._adapters.get(platform, self._adapters["manual"])

    def list_accounts(self, worker_id: str | None = None) -> list[AccountConnection]:
        accs = list(self._accounts.values())
        if worker_id:
            accs = [a for a in accs if a.worker_id == worker_id]
        return accs

    def schedule_publication(
        self,
        task_id: str,
        platform: PlatformType,
        scheduled_at: datetime,
    ) -> ScheduledPublication:
        """Schedule approved content for distribution. Enforces approval gate."""
        task = task_store.get_task(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")

        # CRITICAL SAFETY GATE: Only approved tasks can be scheduled
        if task.status != "completed" and task.approval_required:
            raise ValueError(f"Content requires human operator approval before scheduling. Current status: '{task.status}'")

        if not task.content:
            raise ValueError("Task has no structured content piece to publish")

        schedule_id = str(uuid4())
        record = ScheduledPublication(
            id=schedule_id,
            worker_id=task.worker_id,
            task_id=task.task_id,
            platform=platform,
            status="scheduled",
            scheduled_at=scheduled_at,
            created_at=datetime.now(timezone.utc),
        )
        self._schedule[schedule_id] = record
        audit_service.record("publication.scheduled", "publication", schedule_id, details={
            "worker_id": task.worker_id,
            "platform": platform,
            "scheduled_at": scheduled_at.isoformat(),
        })
        logger.info("Scheduled task %s for platform %s at %s", task_id[:8], platform, scheduled_at)
        return record

    async def publish_now(self, schedule_id: str) -> ScheduledPublication:
        """Trigger immediate publication or generate manual dispatch instructions."""
        record = self._schedule.get(schedule_id)
        if not record:
            raise KeyError(f"Scheduled publication '{schedule_id}' not found")

        task = task_store.get_task(record.task_id)
        if not task or not task.content:
            record.status = "failed"
            record.error_message = "Content piece missing"
            return record

        adapter = self.get_adapter(record.platform)
        account = next(
            (a for a in self._accounts.values() if a.worker_id == record.worker_id and a.platform == record.platform),
            None
        )

        res = await adapter.publish(task.content, account or self._accounts.get(f"acc-{record.worker_id}-manual"))

        record.status = res.get("status", "published")
        record.platform_post_id = res.get("platform_post_id")
        record.platform_url = res.get("platform_url")
        record.manual_instructions = res.get("manual_instructions")
        record.published_at = datetime.now(timezone.utc) if record.status == "published" else None

        audit_service.record("publication.executed", "publication", schedule_id, details={
            "status": record.status,
            "platform": record.platform,
            "platform_url": record.platform_url,
        })
        return record

    def complete_manual_publication(self, schedule_id: str, platform_url: str) -> ScheduledPublication:
        """Mark a manual publication as completed by operator with public URL."""
        record = self._schedule.get(schedule_id)
        if not record:
            raise KeyError(f"Scheduled publication '{schedule_id}' not found")
        record.status = "published"
        record.platform_url = platform_url
        record.published_at = datetime.now(timezone.utc)
        audit_service.record("publication.manual_confirmed", "publication", schedule_id, details={
            "platform_url": platform_url
        })
        return record

    def list_schedule(self, worker_id: str | None = None, status: str | None = None) -> list[ScheduledPublication]:
        items = list(self._schedule.values())
        if worker_id:
            items = [i for i in items if i.worker_id == worker_id]
        if status:
            items = [i for i in items if i.status == status]
        return sorted(items, key=lambda x: x.scheduled_at)

publishing_service = PublishingService()

