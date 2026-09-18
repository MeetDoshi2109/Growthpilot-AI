"""Customer model — tenant-scoped."""
from datetime import date

from sqlalchemy import Boolean, Date, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import SoftDeleteMixin, TimestampMixin, gen_uuid


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Lifecycle
    first_purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spend_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Behavioral (computed and cached, refreshed by analytics engine)
    median_purchase_cadence_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    days_since_last_purchase: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_order_value_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Payment behavior
    failed_payment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_overdue_invoice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Consent
    sms_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    whatsapp_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Tags (free-form JSON-safe string list)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string

    __table_args__ = (
        Index("ix_customers_merchant_last_purchase", "merchant_id", "last_purchase_date"),
        Index("ix_customers_merchant_phone", "merchant_id", "phone"),
        Index("ix_customers_merchant_spend", "merchant_id", "total_spend_paise"),
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name} [{self.merchant_id[:8]}]>"
