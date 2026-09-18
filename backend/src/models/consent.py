"""Consent model — customer messaging opt-in/opt-out."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class Consent(Base, TimestampMixin):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    # sms | whatsapp | email | push

    is_opted_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opted_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opt_out_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_consents_merchant_customer_channel", "merchant_id", "customer_id", "channel"),
    )
