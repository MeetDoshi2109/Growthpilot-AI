"""AuditLog model — append-only, hash-chained."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import gen_uuid


class AuditLog(Base):
    """
    Append-only audit log with hash-chaining for tamper detection.
    Never soft-deleted. Never updated. Only inserted.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Chain integrity
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Event metadata
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(__import__('datetime').timezone.utc),
        index=True
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # agent | merchant | system
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Event details
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # PII-masked input/output
    input_masked: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Decision trail
    policy_result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approval_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    final_result: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Tracing
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_audit_logs_merchant_timestamp", "merchant_id", "timestamp"),
        Index("ix_audit_logs_sequence", "merchant_id", "sequence_number"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.tool} [{self.final_result}]>"
