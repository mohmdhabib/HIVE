from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.schemas.task import TaskRequest, TaskReport, TaskPlan
from app.workers.registry import get_worker
from app.workers.engine import execute_worker_task
from app.services.llm import LLMService
from app.services.task_store import task_store
from app.services.audit import audit_service
from app.master.strategy import prioritize_task
from app.master.evaluator import evaluate_execution
from app.core.exceptions import WorkerDisabledError, KillSwitchActiveError
from app.core.logging import get_logger
from app.config import get_settings

logger = get_logger("master")

class MasterState(TypedDict, total=False):
    request: TaskRequest
    plan: TaskPlan
    llm: LLMService
    report: TaskReport
    error: str

async def check_kill_switch(state: MasterState) -> MasterState:
    settings = get_settings()
    if settings.global_kill_switch:
        audit_service.record("kill_switch.blocked_execution", "system", "global", details={"worker_id": state["request"].worker_id})
        raise KillSwitchActiveError("Global kill switch is active — all operations suspended")
    return state

async def prioritize_and_plan(state: MasterState) -> MasterState:
    plan = prioritize_task(state["request"])
    logger.info("Master planning: priority=%s, tokens=%d", plan.priority, plan.estimated_tokens)
    return {**state, "plan": plan}

async def validate_assignment(state: MasterState) -> MasterState:
    request = state["request"]
    worker = get_worker(request.worker_id)
    if not worker.enabled:
        audit_service.record("worker.assignment_rejected_disabled", "worker", worker.id)
        raise WorkerDisabledError(f"Worker '{worker.name}' is paused or disabled")
    logger.info("Assignment validated for worker '%s' (%s)", worker.name, worker.id)
    return state

async def delegate_to_worker(state: MasterState) -> MasterState:
    report = await execute_worker_task(
        request=state["request"],
        llm=state["llm"],
        plan=state.get("plan"),
    )
    return {**state, "report": report}

async def evaluate_report(state: MasterState) -> MasterState:
    evaluated = evaluate_execution(state["report"])
    # Persist in task storage and record audit trail
    task_store.save_task(evaluated)
    audit_service.record(
        action="task.executed",
        resource_type="task",
        resource_id=evaluated.task_id,
        details={
            "worker_id": evaluated.worker_id,
            "status": evaluated.status,
            "priority": evaluated.priority,
            "quality_score": evaluated.quality_check.score if evaluated.quality_check else None,
        }
    )
    return {**state, "report": evaluated}

_builder = StateGraph(MasterState)
_builder.add_node("check_kill_switch", check_kill_switch)
_builder.add_node("prioritize_and_plan", prioritize_and_plan)
_builder.add_node("validate_assignment", validate_assignment)
_builder.add_node("delegate_to_worker", delegate_to_worker)
_builder.add_node("evaluate_report", evaluate_report)

_builder.set_entry_point("check_kill_switch")
_builder.add_edge("check_kill_switch", "prioritize_and_plan")
_builder.add_edge("prioritize_and_plan", "validate_assignment")
_builder.add_edge("validate_assignment", "delegate_to_worker")
_builder.add_edge("delegate_to_worker", "evaluate_report")
_builder.add_edge("evaluate_report", END)

master_graph = _builder.compile()

async def delegate(request: TaskRequest, llm: LLMService) -> TaskReport:
    """Master Agent entry point: execute the full planning, validation, execution, and evaluation cycle."""
    logger.info("Master Agent initiating workflow for worker=%s", request.worker_id)
    result = await master_graph.ainvoke({"request": request, "llm": llm})
    return result["report"]
