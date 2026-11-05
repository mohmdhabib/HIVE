from typing import TypedDict
from uuid import uuid4
from langgraph.graph import StateGraph, END
from app.schemas.worker import WorkerConfig
from app.schemas.task import TaskRequest, TaskReport, TaskPlan
from app.schemas.content import ContentPiece, QualityCheckResult
from app.schemas.memory import WorkerMemoryContext
from app.services.llm import LLMService
from app.services.memory import memory_service
from app.core.logging import get_logger

logger = get_logger("worker.pipeline")

class PipelineState(TypedDict, total=False):
    worker: WorkerConfig
    request: TaskRequest
    plan: TaskPlan
    llm: LLMService
    memory_context: WorkerMemoryContext
    content: ContentPiece
    quality: QualityCheckResult
    report: TaskReport

async def research_and_angle(state: PipelineState) -> PipelineState:
    """Step 1: Focus content strategy based on brand pillars and inject worker memory history."""
    worker = state["worker"]
    req = state["request"]
    memory_ctx = memory_service.get_worker_context(worker.id)
    logger.info(
        "Pipeline Step 1 (Research): Worker=%s, Recent Topics=%d, Winning Patterns=%d",
        worker.id, len(memory_ctx.recent_topics), len(memory_ctx.successful_patterns)
    )
    return {**state, "memory_context": memory_ctx}

async def generate_content_piece(state: PipelineState) -> PipelineState:
    """Step 2: Generate structured ContentPiece with Pydantic schema validation & memory context."""
    worker = state["worker"]
    req = state["request"]
    llm = state["llm"]
    memory_ctx = state.get("memory_context", WorkerMemoryContext())

    recent_topics_str = ", ".join(memory_ctx.recent_topics) if memory_ctx.recent_topics else "None yet"
    winning_patterns_str = "; ".join(memory_ctx.successful_patterns) if memory_ctx.successful_patterns else "High-retention hooks with clear visual changes"
    cross_insights_str = "; ".join(memory_ctx.cross_worker_insights) if memory_ctx.cross_worker_insights else "None yet"

    prompt = f"""Brand Identity:
- Name: {worker.name}
- Niche: {worker.niche}
- Audience: {worker.audience}
- Voice Guidelines: {worker.voice}
- Content Pillars: {', '.join(worker.content_pillars)}
- Monetization Target: {worker.revenue_target.primary_stream} (Monthly goal: ${worker.revenue_target.monthly_target_usd})

Memory & History (Avoid Repetition):
- Previously Covered Topics: {recent_topics_str} (Do NOT repeat these verbatim)
- Winning Brand Patterns: {winning_patterns_str}
- Cross-Network Insights: {cross_insights_str}

Directive / Master Objective:
{req.objective}

Target Channel: {req.target_platform}

Task Instructions:
1. Create a compelling title and an arresting 3-second hook designed for short-form retention.
2. Write a detailed body script or narration outline.
3. Formulate an engaging caption with 3-5 relevant contextual hashtags.
4. Provide a visual brief detailing camera framing, graphics, overlays, or b-roll.
5. Formulate an explicit monetization hypothesis explaining how this piece converts into affiliate sales, leads, or sponsorships.
6. Clearly list any factual or statistical claims that require human source verification.
7. Assess estimated risk level (low/medium/high) and list any caveats."""

    system_prompt = (
        f"You are the autonomous content engine for {worker.name}. "
        "Strictly adhere to the brand voice and monetization targets. Never invent false facts, fake endorsements, or fabricate data."
    )

    try:
        content = await llm.generate_structured(
            prompt=prompt,
            schema=ContentPiece,
            temperature=0.3,
            system=system_prompt,
        )
    except Exception as exc:
        logger.warning("Structured generation fallback triggered: %s", exc)
        raw = await llm.generate(prompt=prompt, temperature=0.3, system=system_prompt)
        content = ContentPiece(
            title=f"{worker.name} — Content Draft",
            hook=req.objective[:80] + "...",
            body_script=raw,
            caption=f"Latest insights from {worker.name}. #content #hive",
            hashtags=["hive", worker.id, "media"],
            visual_brief="Clean talking-head or b-roll video with bold text overlays.",
            target_platform=req.target_platform,
            monetization_hypothesis=f"Affiliate or sponsor placement targeting {worker.audience}.",
            factual_checks=["Verify all product claims and metrics before publication."],
            estimated_risk_level="low",
            risks_and_caveats=["Requires editorial review."]
        )

    return {**state, "content": content}

async def quality_and_factuality_check(state: PipelineState) -> PipelineState:
    """Step 3: Quality check and risk evaluation."""
    content = state["content"]
    feedback: list[str] = []
    flags: list[str] = []
    score = 1.0

    # Hook criteria
    if len(content.hook.strip()) < 10:
        feedback.append("Hook is too short to capture attention in the first 3 seconds.")
        score -= 0.2

    # Monetization criteria
    if not content.monetization_hypothesis or len(content.monetization_hypothesis) < 15:
        feedback.append("Monetization hypothesis is vague. Every content piece must tie to revenue.")
        score -= 0.3

    # Factual verification requirements
    if content.factual_checks:
        flags.extend([f"Verify claim: {c}" for c in content.factual_checks])

    # Risk level penalties
    if content.estimated_risk_level == "high":
        flags.append("High risk flagged: legal or brand safety review mandatory.")
        score -= 0.2
    elif content.estimated_risk_level == "medium":
        score -= 0.1

    score = max(0.0, min(1.0, score))
    passed = score >= 0.5 and content.estimated_risk_level != "high"

    quality = QualityCheckResult(
        passed=passed,
        score=round(score, 2),
        feedback=feedback or ["Content satisfies brand and editorial guidelines."],
        flags=flags,
    )
    return {**state, "quality": quality}

async def compile_task_report(state: PipelineState) -> PipelineState:
    """Step 4: Package into final TaskReport and update worker memory store."""
    worker = state["worker"]
    req = state["request"]
    content = state["content"]
    quality = state["quality"]
    plan = state.get("plan", TaskPlan())

    task_id = str(uuid4())
    status = "needs_approval" if req.require_approval else "completed"

    report = TaskReport(
        task_id=task_id,
        worker_id=worker.id,
        worker_name=worker.name,
        objective=req.objective,
        status=status,
        content=content,
        output=f"**{content.title}**\n\n**Hook:** {content.hook}\n\n**Script:**\n{content.body_script}\n\n**Caption:** {content.caption}\n\n**Monetization Angle:** {content.monetization_hypothesis}",
        quality_check=quality,
        approval_required=req.require_approval,
        priority=plan.priority,
    )

    # Record to worker isolated memory store
    memory_service.add_entry(
        worker_id=worker.id,
        category="topic_history",
        key=content.title,
        content={"title": content.title, "hook": content.hook, "platform": content.target_platform}
    )

    if quality.passed and quality.score >= 0.8:
        memory_service.add_entry(
            worker_id=worker.id,
            category="successful_pattern",
            key=f"pattern-{task_id[:8]}",
            content={"pattern": f"Effective hook: '{content.hook[:60]}...'", "score": quality.score}
        )

    return {**state, "report": report}

_pipeline_builder = StateGraph(PipelineState)
_pipeline_builder.add_node("research_and_angle", research_and_angle)
_pipeline_builder.add_node("generate_content_piece", generate_content_piece)
_pipeline_builder.add_node("quality_and_factuality_check", quality_and_factuality_check)
_pipeline_builder.add_node("compile_task_report", compile_task_report)

_pipeline_builder.set_entry_point("research_and_angle")
_pipeline_builder.add_edge("research_and_angle", "generate_content_piece")
_pipeline_builder.add_edge("generate_content_piece", "quality_and_factuality_check")
_pipeline_builder.add_edge("quality_and_factuality_check", "compile_task_report")
_pipeline_builder.add_edge("compile_task_report", END)

worker_pipeline_graph = _pipeline_builder.compile()
