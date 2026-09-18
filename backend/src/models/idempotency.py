"""IdempotencyKey model — prevents duplicate action execution."""
from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import gen_uuid


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON cached result

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(__import__("datetime").timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_idempotency_merchant_action", "merchant_id", "action_type"),
    )
