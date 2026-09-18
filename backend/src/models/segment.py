"""CustomerSegment and CustomerScore models."""
from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class CustomerSegment(Base, TimestampMixin):
    __tablename__ = "customer_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # RFM segment label
    segment: Mapped[str] = mapped_column(String(50), nullable=False)
    # champions | loyal | potential_loyalists | at_risk | cant_lose | new_customers | dormant

    # RFM scores (1-5 quintiles)
    recency_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    frequency_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    monetary_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    rfm_total: Mapped[int] = mapped_column(Integer, nullable=False, default=9)

    # Raw RFM values
    recency_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monetary_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Computed at
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(__import__('datetime').timezone.utc)
    )
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    __table_args__ = (
        Index("ix_customer_segments_merchant_segment", "merchant_id", "segment"),
        Index("ix_customer_segments_merchant_customer", "merchant_id", "customer_id"),
    )

    def __repr__(self) -> str:
        return f"<CustomerSegment {self.customer_id[:8]} [{self.segment}]>"


class CustomerScore(Base, TimestampMixin):
    __tablename__ = "customer_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Churn probability (0–1)
    churn_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    churn_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # low | medium | high | critical

    # CLV estimate (paise, 30-day horizon)
    clv_estimate_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Top churn reasons (JSON array of strings)
    top_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model version
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(__import__('datetime').timezone.utc)
    )

    __table_args__ = (
        Index("ix_customer_scores_merchant_risk", "merchant_id", "churn_risk_level"),
        Index("ix_customer_scores_merchant_customer", "merchant_id", "customer_id"),
    )
