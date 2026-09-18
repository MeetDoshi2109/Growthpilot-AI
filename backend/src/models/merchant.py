"""Merchant model — core business entity."""
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import SoftDeleteMixin, TimestampMixin, gen_uuid


class Merchant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. tea_snacks | pharmacy | salon | electronics | restaurant
    vertical: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Paytm-style onboarding fields (all simulated)
    paytm_mid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Monthly GMV in paise (used for financial readiness tier)
    avg_monthly_gmv_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Hero merchant flag for demo
    is_demo_hero: Mapped[bool] = mapped_column(
        "is_demo_hero", String(5), default=False, nullable=False
    )

    __table_args__ = (
        Index("ix_merchants_vertical", "vertical"),
        Index("ix_merchants_city", "city"),
    )

    def __repr__(self) -> str:
        return f"<Merchant {self.name} [{self.vertical}]>"
