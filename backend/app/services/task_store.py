from datetime import datetime, timezone
from app.schemas.task import TaskReport
from app.core.logging import get_logger

logger = get_logger("task_store")

class TaskStoreService:
    """Manages persistent execution reports, status transitions, and approval workflows."""

    def __init__(self):
        self._tasks: dict[str, TaskReport] = {}

    def save_task(self, report: TaskReport) -> TaskReport:
        """Persist or update a task report."""
        self._tasks[report.task_id] = report
        logger.info("Saved task %s, worker=%s, status=%s", report.task_id[:8], report.worker_id, report.status)
        return report

    def get_task(self, task_id: str) -> TaskReport | None:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        worker_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[TaskReport]:
        """List tasks ordered by creation time."""
        tasks = list(self._tasks.values())
        if worker_id:
            tasks = [t for t in tasks if t.worker_id == worker_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)[:limit]

    def approve_task(self, task_id: str, operator: str = "operator") -> TaskReport:
        """Approve a pending task."""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")
        task.status = "completed"
        task.approval_required = False
        return task

    def reject_task(self, task_id: str, reason: str = "Operator rejected", operator: str = "operator") -> TaskReport:
        """Reject a pending task."""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")
        task.status = "failed"
        if task.quality_check:
            task.quality_check.feedback.append(f"Rejected by operator: {reason}")
        return task

# Global singleton service
task_store = TaskStoreService()

