"""GrowthOpportunity model."""
from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class GrowthOpportunity(Base, TimestampMixin):
    __tablename__ = "growth_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Opportunity classification
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # CUSTOMER_WINBACK | CROSS_SELL | UPSELL | PRODUCT_PROMOTION | INVENTORY_RISK
    # PAYMENT_RECOVERY | CUSTOMER_RETENTION | REVENUE_DECLINE | HIGH_VALUE_CUSTOMER
    # SEASONAL_OPPORTUNITY

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Evidence (JSON array of evidence objects)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Targeting
    affected_customers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_customer_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    # Impact estimation (in paise)
    estimated_impact_low_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_impact_base_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_impact_high_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Confidence (0–1)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    # Priority (1 = highest)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Recommended action
    recommended_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Approval requirements
    requires_approval: Mapped[bool] = mapped_column(String(5), nullable=False, default=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    # active | actioned | dismissed | expired

    data_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Explainability (JSON)
    explainability: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_growth_opportunities_merchant_status", "merchant_id", "status"),
        Index("ix_growth_opportunities_merchant_type", "merchant_id", "opportunity_type"),
        Index("ix_growth_opportunities_merchant_priority", "merchant_id", "priority"),
    )

    def __repr__(self) -> str:
        return f"<GrowthOpportunity {self.opportunity_type} [{self.status}]>"
