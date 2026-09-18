"""AutonomySetting model — merchant autonomy dial and kill switch."""
from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class AutonomySetting(Base, TimestampMixin):
    __tablename__ = "autonomy_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)

    # Autonomy level: off | recommend | semi_auto | full_auto
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="recommend")

    # Kill switch
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kill_switch_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Contact limits
    max_daily_contacts_per_customer: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_weekly_contacts_per_customer: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Quiet hours (24h format): no outbound messaging between these hours
    quiet_hours_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0=disabled
    quiet_hours_end: Mapped[int] = mapped_column(Integer, nullable=False, default=0)    # 0=disabled

    __table_args__ = (
        Index("ix_autonomy_settings_merchant", "merchant_id"),
    )
