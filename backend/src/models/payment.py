"""Payment model — overdue tracking and recovery."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    invoice_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | paid | overdue | partial | written_off

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 0 = not overdue; computed and refreshed by analytics engine

    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Recovery tracking
    reminder_sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reminder_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_simulated_link: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_payments_merchant_status", "merchant_id", "status"),
        Index("ix_payments_merchant_due", "merchant_id", "due_date"),
        Index("ix_payments_merchant_overdue", "merchant_id", "days_overdue"),
    )
