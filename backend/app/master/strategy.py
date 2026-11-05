from app.schemas.task import TaskRequest, TaskPlan, TaskPriority

def prioritize_task(request: TaskRequest) -> TaskPlan:
    """Analyze incoming directive to determine priority, token budget, and approval requirements."""
    objective_lower = request.objective.lower()

    # Determine priority
    priority: TaskPriority = "medium"
    if any(k in objective_lower for k in ["breaking", "urgent", "crisis", "critical", "immediate"]):
        priority = "critical"
    elif any(k in objective_lower for k in ["sponsor", "affiliate", "campaign", "revenue", "partnership"]):
        priority = "high"
    elif any(k in objective_lower for k in ["backlog", "low priority", "evergreen", "idea"]):
        priority = "low"

    # Token allocation estimate based on platform and priority
    token_map = {
        "x": 800,
        "instagram": 1400,
        "youtube_shorts": 1800,
        "facebook": 1200,
    }
    estimated_tokens = token_map.get(request.target_platform, 1500)
    if priority == "high":
        estimated_tokens += 500

    rationale = f"Evaluated for channel={request.target_platform} with priority={priority}."

    return TaskPlan(
        priority=priority,
        rationale=rationale,
        estimated_tokens=estimated_tokens,
        approval_gates=["editorial_review", "compliance_check"] if request.require_approval else []
    )

