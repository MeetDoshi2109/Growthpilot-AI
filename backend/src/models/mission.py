"""Mission and MissionStep models — Track 3 autonomous agent missions."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class Mission(Base, TimestampMixin):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | running | awaiting_approval | completed | failed | cancelled | paused

    plan: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON step list
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    step_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=120)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_impact_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_missions_merchant_status", "merchant_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Mission {self.title[:30]} [{self.status}]>"


class MissionStep(Base, TimestampMixin):
    __tablename__ = "mission_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    mission_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | running | awaiting_approval | done | failed | skipped

    depends_on: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of step numbers

    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_mission_steps_mission", "mission_id", "step_number"),
    )
