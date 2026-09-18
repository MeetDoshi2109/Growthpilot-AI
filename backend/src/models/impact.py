"""ImpactMeasurement model — Proof of Impact control-group results."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class ImpactMeasurement(Base, TimestampMixin):
    __tablename__ = "impact_measurements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    measurement_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    measurement_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Treatment group
    treatment_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    treatment_conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    treatment_revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    treatment_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Control group
    control_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    control_conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    control_revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    control_conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Lift
    incremental_conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    incremental_revenue_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lift_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    lift_ci_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    lift_ci_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_statistically_significant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_inconclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Beta-Binomial posteriors for learning loop
    beta_alpha_prior: Mapped[float | None] = mapped_column(Float, nullable=True)
    beta_beta_prior: Mapped[float | None] = mapped_column(Float, nullable=True)
    beta_alpha_posterior: Mapped[float | None] = mapped_column(Float, nullable=True)
    beta_beta_posterior: Mapped[float | None] = mapped_column(Float, nullable=True)

    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_impact_measurements_merchant", "merchant_id"),
        Index("ix_impact_measurements_campaign", "campaign_id"),
    )
