"""FinancialProfile model — cash-flow and readiness scoring."""
from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class FinancialProfile(Base, TimestampMixin):
    __tablename__ = "financial_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, unique=True)

    # Revenue metrics (paise)
    avg_monthly_revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    # coefficient of variation — lower = more stable

    # Cash flow trend
    cash_flow_trend: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # improving | stable | declining

    # Transaction consistency (0–1)
    transaction_consistency: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Collection behavior
    collection_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    overdue_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_days_to_collect: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Growth score (0–100)
    business_growth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_history_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Overall financial readiness score (0–100) — labeled "Demo eligibility"
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # strong | good | fair | needs_improvement

    # Factor contributions (JSON)
    factor_contributions: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Data window used
    analysis_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(__import__('datetime').timezone.utc)
    )

    __table_args__ = (
        Index("ix_financial_profiles_merchant", "merchant_id"),
    )
