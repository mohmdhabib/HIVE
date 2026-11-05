from app.schemas.task import TaskRequest, TaskReport, TaskPlan
from app.workers.registry import get_worker
from app.workers.pipeline import worker_pipeline_graph
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger("worker.engine")

async def execute_worker_task(
    request: TaskRequest,
    llm: LLMService,
    plan: TaskPlan | None = None
) -> TaskReport:
    """Execute a task through the stateful multi-stage worker pipeline."""
    worker = get_worker(request.worker_id)
    logger.info("Executing worker pipeline for worker=%s (%s)", worker.id, worker.name)

    initial_state = {
        "worker": worker,
        "request": request,
        "plan": plan or TaskPlan(),
        "llm": llm,
    }

    result = await worker_pipeline_graph.ainvoke(initial_state)
    report = result["report"]
    logger.info("Worker pipeline completed for task %s, status=%s", report.task_id[:8], report.status)
    return report
