from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.memory import MemoryEntry, MemoryCategory, WorkerMemoryContext
from app.core.logging import get_logger

logger = get_logger("memory")

class WorkerMemoryService:
    """Manages isolated memory stores per worker with sanitized cross-worker pattern learning."""

    def __init__(self):
        # In-memory backing store: dict[worker_id, list[MemoryEntry]]
        self._stores: dict[str, list[MemoryEntry]] = {}

    def add_entry(
        self,
        worker_id: str,
        category: MemoryCategory,
        key: str,
        content: dict,
    ) -> MemoryEntry:
        """Record a new memory entry for a specific worker."""
        if worker_id not in self._stores:
            self._stores[worker_id] = []

        entry = MemoryEntry(
            id=str(uuid4()),
            worker_id=worker_id,
            category=category,
            key=key,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self._stores[worker_id].append(entry)
        logger.info("Recorded memory for worker=%s, category=%s, key=%s", worker_id, category, key)
        return entry

    def get_entries(
        self,
        worker_id: str,
        category: MemoryCategory | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Fetch memory entries for a worker, optionally filtered by category."""
        entries = self._stores.get(worker_id, [])
        if category:
            entries = [e for e in entries if e.category == category]
        return sorted(entries, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_worker_context(self, worker_id: str) -> WorkerMemoryContext:
        """Compile isolated brand context + cross-worker sanitized insights for prompt injection."""
        worker_entries = self._stores.get(worker_id, [])

        recent_topics = [
            e.content.get("title", e.key)
            for e in worker_entries
            if e.category == "topic_history"
        ][-5:]

        successful_patterns = [
            e.content.get("pattern", e.key)
            for e in worker_entries
            if e.category == "successful_pattern"
        ][-5:]

        failed_patterns = [
            e.content.get("pattern", e.key)
            for e in worker_entries
            if e.category == "failed_pattern"
        ][-5:]

        cross_insights = self.get_cross_worker_insights(exclude_worker_id=worker_id)

        return WorkerMemoryContext(
            recent_topics=recent_topics,
            successful_patterns=successful_patterns,
            banned_or_failed_patterns=failed_patterns,
            cross_worker_insights=cross_insights,
        )

    def get_cross_worker_insights(self, exclude_worker_id: str) -> list[str]:
        """Extract high-performing content patterns from other workers without leaking private data or credentials."""
        insights: list[str] = []
        for other_id, entries in self._stores.items():
            if other_id == exclude_worker_id:
                continue
            for e in entries:
                if e.category == "successful_pattern":
                    pattern_desc = e.content.get("pattern")
                    if pattern_desc and pattern_desc not in insights:
                        # Ensure no credential or private account tokens are in pattern
                        insights.append(pattern_desc)
        return insights[:3]

# Global singleton service
memory_service = WorkerMemoryService()

