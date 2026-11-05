from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

RevenueStream = Literal["affiliate", "sponsorship", "lead_gen", "digital_product", "platform_creator_fund"]
AttributionType = Literal["measured", "imported", "estimated"]
CostType = Literal["llm_compute", "hosting_infra", "media_storage", "platform_fee"]

class RevenueEvent(BaseModel):
    """Verifiable revenue event attributed to a specific worker, platform, or content piece."""
    id: str
    worker_id: str
    task_id: str | None = None
    platform: str
    stream: RevenueStream
    gross_amount: float = Field(ge=0.0, description="Gross revenue amount in USD")
    currency: str = "USD"
    attribution_type: AttributionType = Field(
        default="measured",
        description="Explicit attribution status: measured (direct webhook), imported (CSV/API), or estimated (RPM model)"
    )
    campaign_id: str | None = None
    conversion_metadata: dict = Field(default_factory=dict, description="Clicks, conversions, sponsor name, or SKU")
    verified: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CostEvent(BaseModel):
    """Production or infrastructure cost item."""
    id: str
    worker_id: str | None = None
    task_id: str | None = None
    cost_type: CostType
    amount: float = Field(ge=0.0, description="Cost amount in USD")
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkerProfitability(BaseModel):
    """Attributed financial performance of a single worker brand."""
    worker_id: str
    worker_name: str
    gross_revenue: float
    total_costs: float
    net_profit: float
    profit_margin_pct: float
    monthly_target_usd: float
    target_progress_pct: float
    primary_stream: str
    measured_revenue: float
    estimated_revenue: float

class FinancialSummary(BaseModel):
    """Network-wide executive revenue and profitability summary."""
    total_gross_revenue: float
    total_costs: float
    net_profit: float
    profit_margin_pct: float
    stream_breakdown: dict[str, float]
    attribution_breakdown: dict[str, float]
    worker_rankings: list[WorkerProfitability]
    recent_events: list[RevenueEvent]

