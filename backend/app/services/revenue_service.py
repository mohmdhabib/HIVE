from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.schemas.revenue import (
    RevenueEvent,
    CostEvent,
    WorkerProfitability,
    FinancialSummary,
    RevenueStream,
    AttributionType,
    CostType,
)
from app.workers.registry import list_workers, get_worker
from app.services.audit import audit_service
from app.core.logging import get_logger

logger = get_logger("revenue_service")

class RevenueService:
    """Core financial attribution, cost tracking, and profitability engine."""

    def __init__(self):
        self._revenue_events: list[RevenueEvent] = []
        self._cost_events: list[CostEvent] = []
        self._seed_financial_data()

    def _seed_financial_data(self):
        """Seed initial verifiable revenue events and production costs across worker operations."""
        now = datetime.now(timezone.utc)

        # 1. Signal Tech (Affiliate & SaaS Sponsorships)
        self._revenue_events.extend([
            RevenueEvent(
                id="rev-tech-01",
                worker_id="tech",
                platform="instagram",
                stream="affiliate",
                gross_amount=342.50,
                attribution_type="measured",
                conversion_metadata={"source": "Cursor / Warp dev tool referral", "clicks": 218, "conversions": 14},
                created_at=now - timedelta(days=2),
            ),
            RevenueEvent(
                id="rev-tech-02",
                worker_id="tech",
                platform="youtube",
                stream="sponsorship",
                gross_amount=1200.00,
                attribution_type="measured",
                conversion_metadata={"sponsor": "CloudHost AI GPU", "contract_id": "SPON-2026-08"},
                created_at=now - timedelta(days=5),
            ),
            RevenueEvent(
                id="rev-tech-03",
                worker_id="tech",
                platform="x",
                stream="affiliate",
                gross_amount=185.00,
                attribution_type="imported",
                conversion_metadata={"network": "Impact.com", "product": "LLM API credits"},
                created_at=now - timedelta(days=8),
            ),
        ])

        # 2. Founder Brief (Sponsorships & B2B Leads)
        self._revenue_events.extend([
            RevenueEvent(
                id="rev-biz-01",
                worker_id="business",
                platform="x",
                stream="sponsorship",
                gross_amount=1500.00,
                attribution_type="measured",
                conversion_metadata={"sponsor": "Stripe Atlas partner package", "placements": 2},
                created_at=now - timedelta(days=3),
            ),
            RevenueEvent(
                id="rev-biz-02",
                worker_id="business",
                platform="youtube",
                stream="lead_gen",
                gross_amount=450.00,
                attribution_type="measured",
                conversion_metadata={"client": "Venture advisory consults", "leads_captured": 9},
                created_at=now - timedelta(days=6),
            ),
        ])

        # 3. Culture Loop (Creator Fund & Digital Products)
        self._revenue_events.extend([
            RevenueEvent(
                id="rev-ent-01",
                worker_id="entertainment",
                platform="youtube",
                stream="platform_creator_fund",
                gross_amount=215.80,
                attribution_type="imported",
                conversion_metadata={"views": 182000, "rpm": 1.18},
                created_at=now - timedelta(days=1),
            ),
            RevenueEvent(
                id="rev-ent-02",
                worker_id="entertainment",
                platform="instagram",
                stream="digital_product",
                gross_amount=389.00,
                attribution_type="measured",
                conversion_metadata={"product": "Viral Video CapCut Template Pack", "units": 41},
                created_at=now - timedelta(days=4),
            ),
        ])

        # 4. Curiosity Daily (Affiliate Books & Course Referrals)
        self._revenue_events.extend([
            RevenueEvent(
                id="rev-edu-01",
                worker_id="education",
                platform="instagram",
                stream="affiliate",
                gross_amount=412.00,
                attribution_type="measured",
                conversion_metadata={"network": "Amazon Associates + Audible", "items_sold": 88},
                created_at=now - timedelta(days=2),
            ),
            RevenueEvent(
                id="rev-edu-02",
                worker_id="education",
                platform="youtube",
                stream="affiliate",
                gross_amount=320.00,
                attribution_type="estimated",
                conversion_metadata={"model": "Projected course referral commission based on traffic"},
                created_at=now - timedelta(days=7),
            ),
        ])

        # 5. Everyday Edit (Gear Affiliate)
        self._revenue_events.extend([
            RevenueEvent(
                id="rev-life-01",
                worker_id="lifestyle",
                platform="instagram",
                stream="affiliate",
                gross_amount=560.40,
                attribution_type="measured",
                conversion_metadata={"network": "RewardStyle / LTK", "orders": 34},
                created_at=now - timedelta(days=3),
            ),
            RevenueEvent(
                id="rev-life-02",
                worker_id="lifestyle",
                platform="x",
                stream="affiliate",
                gross_amount=210.00,
                attribution_type="imported",
                conversion_metadata={"store": "Minimalist Desk Pad brand affiliate"},
                created_at=now - timedelta(days=9),
            ),
        ])

        # Production Costs
        self._cost_events.extend([
            CostEvent(
                id="cost-01",
                worker_id="tech",
                cost_type="llm_compute",
                amount=14.50,
                description="Local Ollama GPU compute & token generation power",
                created_at=now - timedelta(days=1),
            ),
            CostEvent(
                id="cost-02",
                worker_id="business",
                cost_type="llm_compute",
                amount=12.20,
                description="Ollama Llama 3.1 inference batching",
                created_at=now - timedelta(days=1),
            ),
            CostEvent(
                id="cost-03",
                worker_id=None,
                cost_type="hosting_infra",
                amount=25.00,
                description="Docker host & Redis memory queue server allocation",
                created_at=now - timedelta(days=1),
            ),
            CostEvent(
                id="cost-04",
                worker_id=None,
                cost_type="media_storage",
                amount=8.50,
                description="Storage volume assets for video & temporary media",
                created_at=now - timedelta(days=2),
            ),
        ])

    def record_revenue(
        self,
        worker_id: str,
        platform: str,
        stream: RevenueStream,
        gross_amount: float,
        attribution_type: AttributionType = "measured",
        campaign_id: str | None = None,
        task_id: str | None = None,
        conversion_metadata: dict | None = None,
    ) -> RevenueEvent:
        """Record verified revenue event attributed to a brand and platform."""
        get_worker(worker_id)  # validate worker exists
        event_id = str(uuid4())
        event = RevenueEvent(
            id=event_id,
            worker_id=worker_id,
            task_id=task_id,
            platform=platform,
            stream=stream,
            gross_amount=round(gross_amount, 2),
            attribution_type=attribution_type,
            campaign_id=campaign_id,
            conversion_metadata=conversion_metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        self._revenue_events.append(event)
        audit_service.record("revenue.recorded", "revenue", event_id, details={
            "worker_id": worker_id,
            "amount": gross_amount,
            "stream": stream,
            "attribution_type": attribution_type,
        })
        logger.info("Recorded revenue event: worker=%s, amount=$%.2f, stream=%s", worker_id, gross_amount, stream)
        return event

    def record_cost(
        self,
        cost_type: CostType,
        amount: float,
        description: str,
        worker_id: str | None = None,
        task_id: str | None = None,
    ) -> CostEvent:
        """Record an operational or compute cost."""
        cost_id = str(uuid4())
        event = CostEvent(
            id=cost_id,
            worker_id=worker_id,
            task_id=task_id,
            cost_type=cost_type,
            amount=round(amount, 2),
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        self._cost_events.append(event)
        audit_service.record("cost.recorded", "cost", cost_id, details={
            "worker_id": worker_id,
            "amount": amount,
            "cost_type": cost_type,
        })
        return event

    def calculate_worker_profitability(self, worker_id: str) -> WorkerProfitability:
        """Calculate exact net profitability, costs, and target progress for a specific worker."""
        worker = get_worker(worker_id)
        worker_revs = [e for e in self._revenue_events if e.worker_id == worker_id]
        worker_costs = [c for c in self._cost_events if c.worker_id == worker_id]

        gross_rev = sum(e.gross_amount for e in worker_revs)
        total_costs = sum(c.amount for c in worker_costs)
        # Allocate shared infra cost proportionally (1/5th to each worker)
        shared_infra_costs = sum(c.amount for c in self._cost_events if c.worker_id is None) / 5.0
        allocated_costs = round(total_costs + shared_infra_costs, 2)

        net_profit = round(gross_rev - allocated_costs, 2)
        margin = round((net_profit / gross_rev * 100), 1) if gross_rev > 0 else 0.0

        target = worker.revenue_target.monthly_target_usd
        progress = round((gross_rev / target * 100), 1) if target > 0 else 0.0

        measured_rev = sum(e.gross_amount for e in worker_revs if e.attribution_type == "measured")
        estimated_rev = sum(e.gross_amount for e in worker_revs if e.attribution_type == "estimated")

        return WorkerProfitability(
            worker_id=worker.id,
            worker_name=worker.name,
            gross_revenue=round(gross_rev, 2),
            total_costs=allocated_costs,
            net_profit=net_profit,
            profit_margin_pct=margin,
            monthly_target_usd=target,
            target_progress_pct=progress,
            primary_stream=worker.revenue_target.primary_stream,
            measured_revenue=round(measured_rev, 2),
            estimated_revenue=round(estimated_rev, 2),
        )

    def get_financial_summary(self) -> FinancialSummary:
        """Calculate network-wide revenue metrics, stream distribution, and worker leaderboard."""
        workers = list_workers()
        worker_profitability = [self.calculate_worker_profitability(w.id) for w in workers]
        # Rank workers by net profit descending
        ranked_workers = sorted(worker_profitability, key=lambda x: x.net_profit, reverse=True)

        total_gross = sum(e.gross_amount for e in self._revenue_events)
        total_costs = sum(c.amount for c in self._cost_events)
        net_profit = round(total_gross - total_costs, 2)
        margin_pct = round((net_profit / total_gross * 100), 1) if total_gross > 0 else 0.0

        # Stream breakdown
        stream_breakdown: dict[str, float] = {}
        for e in self._revenue_events:
            stream_breakdown[e.stream] = round(stream_breakdown.get(e.stream, 0.0) + e.gross_amount, 2)

        # Attribution type breakdown
        attribution_breakdown: dict[str, float] = {}
        for e in self._revenue_events:
            attribution_breakdown[e.attribution_type] = round(
                attribution_breakdown.get(e.attribution_type, 0.0) + e.gross_amount, 2
            )

        recent_events = sorted(self._revenue_events, key=lambda x: x.created_at, reverse=True)[:25]

        return FinancialSummary(
            total_gross_revenue=round(total_gross, 2),
            total_costs=round(total_costs, 2),
            net_profit=net_profit,
            profit_margin_pct=margin_pct,
            stream_breakdown=stream_breakdown,
            attribution_breakdown=attribution_breakdown,
            worker_rankings=ranked_workers,
            recent_events=recent_events,
        )

revenue_service = RevenueService()

