"""Campaign and CampaignRecipient models."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # winback | retention | upsell | cross_sell | promotion | payment_recovery

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    # draft | scheduled | running | completed | cancelled | paused

    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="sms")
    # sms | whatsapp | push | email

    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    offer_amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offer_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Targeting
    target_segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_customer_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    estimated_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Impact estimation (from opportunity engine)
    estimated_impact_low_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_impact_base_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_impact_high_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_response_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Execution
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Simulation flag
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Control group
    control_group_fraction: Mapped[float] = mapped_column(Float, nullable=False, default=0.20)

    __table_args__ = (
        Index("ix_campaigns_merchant_status", "merchant_id", "status"),
        Index("ix_campaigns_merchant_type", "merchant_id", "campaign_type"),
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.name} [{self.status}]>"


class CampaignRecipient(Base, TimestampMixin):
    __tablename__ = "campaign_recipients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Group assignment
    is_control: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Delivery status
    delivery_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | sent | delivered | failed | opted_out

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Outcome
    converted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    conversion_amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_campaign_recipients_campaign", "campaign_id", "customer_id"),
        Index("ix_campaign_recipients_merchant", "merchant_id", "campaign_id"),
    )
