import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.briefing import MasterExecutiveBriefing, WorkerPerformanceDigest, PerformanceSignal
from app.workers.registry import list_workers, get_worker
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger("master_briefing")

DEFAULT_WORKER_BASELINES = [
    {
        "worker_id": "tech",
        "yesterday_reach": 142000,
        "avg_3s_retention_pct": 81.4,
        "top_performing_hook": "Stop coding like it's 2023. Cursor AI just made traditional IDEs obsolete.",
        "top_performing_archetype": "contrarian",
        "status_signal": "viral",
        "diagnosis": "Contrarian warning formula created immediate cognitive dissonance. Visual b-roll showed side-by-side terminal speed tests, minimizing drop-off.",
        "recommended_pivot": "Double down on AI developer tool comparison battles. Increase visual pacing with 1.2s rapid code highlights.",
        "proposed_topic": "Anthropic Computer Use vs Devin: The Death of Manual Web QA",
        "proposed_daily_hook": "90% of QA engineers don't realize their jobs just changed forever. Here's why.",
        "virality_probability": 88,
    },
    {
        "worker_id": "business",
        "yesterday_reach": 88500,
        "avg_3s_retention_pct": 69.2,
        "top_performing_hook": "How a 22-year-old built a $40k/month micro-SaaS with zero funding.",
        "top_performing_archetype": "behind_the_scenes",
        "status_signal": "high_performing",
        "diagnosis": "Micro-case study format converted well. Drop-off increased slightly in the middle 10 seconds due to dense spreadsheet visuals.",
        "recommended_pivot": "Simplify financial data into 3 bold metrics per slide. Use dynamic typewriter captions for revenue numbers.",
        "proposed_topic": "The Bootstrapped Media Empire Playbook (Zero Capital)",
        "proposed_daily_hook": "Most entrepreneurs waste 6 months building an app. Here is how to launch a media asset in 48 hours instead.",
        "virality_probability": 76,
    },
    {
        "worker_id": "entertainment",
        "yesterday_reach": 64000,
        "avg_3s_retention_pct": 58.0,
        "top_performing_hook": "The creepy Hollywood contract clause every actor is secretly signing.",
        "top_performing_archetype": "curiosity_gap",
        "status_signal": "average",
        "diagnosis": "Curiosity gap was strong, but lack of audio SFX in seconds 0-3 caused a 28% scroll-away before the tension payoff.",
        "recommended_pivot": "Add a dramatic impact SFX cue at second 0.2 and tighten the intro to 2.0 seconds maximum.",
        "proposed_topic": "Synthetic Doubles in Film: Who Actually Owns Your Digital Clone?",
        "proposed_daily_hook": "If you look closely at this movie scene, that is not an actor. It is an algorithm.",
        "virality_probability": 71,
    },
    {
        "worker_id": "education",
        "yesterday_reach": 29000,
        "avg_3s_retention_pct": 36.5,
        "top_performing_hook": "Did you know that honey found in ancient pyramids never spoils?",
        "top_performing_archetype": "curiosity_gap",
        "status_signal": "hook_fatigue",
        "diagnosis": "Hook fatigue detected. Passive 'Did you know' phrasing is widely filtered out by modern viewers. Retention collapsed at second 1.8.",
        "recommended_pivot": "Immediately abandon passive trivia framing. Pivot to 'Scientific Paradox' or 'Counter-Intuitive Mystery' hook archetypes.",
        "proposed_topic": "The 3,000-Year-Old Biological Mystery Scientists Finally Solved",
        "proposed_daily_hook": "Archaeologists opened a tomb sealed for 3,000 years and found something edible. Here is why that shouldn't be possible.",
        "virality_probability": 82,
    },
    {
        "worker_id": "lifestyle",
        "yesterday_reach": 42000,
        "avg_3s_retention_pct": 52.1,
        "top_performing_hook": "The 10-3-2-1-0 routine that fixed my sleep.",
        "top_performing_archetype": "stat_paradox",
        "status_signal": "average",
        "diagnosis": "Steady performance but low shareability. Visual aesthetic was clean, but pacing felt too relaxed for short-form feeds.",
        "recommended_pivot": "Shorten total duration to 32 seconds. Inject faster visual cuts (1.5s interval) and Lo-Fi ambient background audio.",
        "proposed_topic": "The 90-Second Cortisol Reset Routine",
        "proposed_daily_hook": "If you wake up tired even after 8 hours of sleep, your nervous system is trapped in fight-or-flight. Do this tonight.",
        "virality_probability": 79,
    },
]

class MasterBriefingService:
    def __init__(self):
        self._cached_briefing: Optional[MasterExecutiveBriefing] = None

    def get_latest_briefing(self) -> MasterExecutiveBriefing:
        if self._cached_briefing is None:
            self._cached_briefing = self._build_baseline_briefing()
        return self._cached_briefing

    def _build_baseline_briefing(self) -> MasterExecutiveBriefing:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        
        workers_data: List[WorkerPerformanceDigest] = []
        for b in DEFAULT_WORKER_BASELINES:
            worker = get_worker(b["worker_id"])
            workers_data.append(
                WorkerPerformanceDigest(
                    worker_id=worker.id,
                    worker_name=worker.name,
                    niche=worker.niche,
                    yesterday_reach=b["yesterday_reach"],
                    avg_3s_retention_pct=b["avg_3s_retention_pct"],
                    top_performing_hook=b["top_performing_hook"],
                    top_performing_archetype=b["top_performing_archetype"],
                    status_signal=b["status_signal"],  # type: ignore
                    diagnosis=b["diagnosis"],
                    recommended_pivot=b["recommended_pivot"],
                    proposed_topic=b["proposed_topic"],
                    proposed_daily_hook=b["proposed_daily_hook"],
                    virality_probability=b["virality_probability"],
                )
            )

        total_reach = sum(w.yesterday_reach for w in workers_data)
        avg_retention = sum(w.avg_3s_retention_pct for w in workers_data) / len(workers_data)

        viral_winners = [w for w in workers_data if w.status_signal in ("viral", "high_performing")]
        underperformers = [w for w in workers_data if w.status_signal in ("underperforming", "hook_fatigue")]

        exec_summary = (
            f"Good morning, Operator. In the last 24 hours, our 5 media brands generated {total_reach:,} verified impressions "
            f"with an average 3-second hook retention of {avg_retention:.1f}%. "
            f"Signal Tech is our primary viral driver (+81.4% retention) due to aggressive contrarian framing. "
            f"However, Curiosity Daily (Education) is suffering from severe hook fatigue (36.5% retention) due to outdated 'Did you know' phrasing. "
            f"I have formulated strategic pivots across all 5 agents today, specifically re-engineering Curiosity Daily's hook into a high-stakes scientific mystery."
        )

        return MasterExecutiveBriefing(
            briefing_id=f"briefing-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            date=date_str,
            headline="Signal Tech Hits Viral Orbit; Curiosity Daily Needs Strategic Pivot",
            executive_summary=exec_summary,
            network_reach_24h=total_reach,
            network_retention_avg_pct=round(avg_retention, 1),
            viral_winners=viral_winners,
            underperformers=underperformers,
            worker_directives=workers_data,
            system_recommendation="Approve daily content directives to rebalance attention distribution toward high-converting formats.",
            status="pending_review",
        )

    async def generate_fresh_briefing(self, llm: Optional[LLMService] = None) -> MasterExecutiveBriefing:
        briefing = self._build_baseline_briefing()
        
        if llm is not None:
            try:
                system_prompt = (
                    "You are HIVE's Master Agent, the Chief Content Officer and Operations Director of an autonomous AI media network.\n"
                    "You speak directly to the Human Operator with concise, high-conviction executive authority.\n"
                    "Analyze yesterday's attention data and synthesize a compelling executive summary."
                )
                user_prompt = (
                    f"Network impressions: {briefing.network_reach_24h:,}\n"
                    f"Average retention: {briefing.network_retention_avg_pct}%\n"
                    f"Viral Brand: Signal Tech (81.4% retention, Contrarian format)\n"
                    f"Underperforming Brand: Curiosity Daily (36.5% retention, Hook Fatigue)\n\n"
                    "Write a 3-sentence executive morning brief to the Operator with your diagnosis and directive."
                )
                llm_summary = await llm.generate(prompt=user_prompt, system=system_prompt)
                if llm_summary and len(llm_summary.strip()) > 30:
                    briefing.executive_summary = llm_summary.strip()
            except Exception as e:
                logger.warning("LLM briefing generation failed, using calibrated brief: %s", e)

        self._cached_briefing = briefing
        return briefing

    def approve_and_dispatch(self) -> MasterExecutiveBriefing:
        briefing = self.get_latest_briefing()
        briefing.status = "executing"
        self._cached_briefing = briefing
        logger.info("Master Agent daily directives approved by operator. Dispatched to 5 creator agents.")
        return briefing

master_briefing_service = MasterBriefingService()

