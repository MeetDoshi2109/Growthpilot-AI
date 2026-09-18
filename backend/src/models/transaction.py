"""Transaction model — individual purchase events."""
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Amount in paise
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Payment details
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    # upi | card | wallet | cash | netbanking | bnpl
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    # success | failed | pending | refunded

    # UPI/payment reference
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamp
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(__import__('datetime').timezone.utc),
    )

    __table_args__ = (
        Index("ix_transactions_merchant_date", "merchant_id", "transaction_date"),
        Index("ix_transactions_merchant_customer", "merchant_id", "customer_id"),
        Index("ix_transactions_merchant_status", "merchant_id", "payment_status"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.amount_paise}p [{self.payment_status}]>"
