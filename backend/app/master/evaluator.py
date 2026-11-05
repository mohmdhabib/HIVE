from app.schemas.task import TaskReport
from app.core.logging import get_logger

logger = get_logger("master.evaluator")

def evaluate_execution(report: TaskReport) -> TaskReport:
    """Master Agent evaluation of worker report before presenting to operator."""
    logger.info("Evaluating report for worker=%s, task=%s", report.worker_id, report.task_id[:8])

    # If content has high risk or multiple factual checks, mandate human approval
    if report.content and (
        report.content.estimated_risk_level == "high" or len(report.content.factual_checks) >= 3
    ):
        report.approval_required = True
        report.status = "needs_approval"
        logger.warning(
            "Task %s flagged for mandatory approval due to high risk or %d unverified facts",
            report.task_id[:8],
            len(report.content.factual_checks),
        )

    # Check quality check result
    if report.quality_check and not report.quality_check.passed:
        logger.warning(
            "Task %s failed quality check (score=%.2f): %s",
            report.task_id[:8],
            report.quality_check.score,
            ", ".join(report.quality_check.feedback),
        )

    return report

