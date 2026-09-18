"""Inventory model — stock tracking per product."""
from datetime import date
from sqlalchemy import Date, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Current stock levels
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Demand analytics (computed by analytics engine, cached here)
    avg_daily_demand: Mapped[float | None] = mapped_column(Float, nullable=True)
    days_until_stockout: Mapped[float | None] = mapped_column(Float, nullable=True)
    demand_forecast_7d: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Lead time info
    supplier_lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    safety_stock_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # Last restock
    last_restocked_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_inventory_merchant_product", "merchant_id", "product_id", unique=True),
        Index("ix_inventory_merchant_stockout", "merchant_id", "days_until_stockout"),
    )

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    def __repr__(self) -> str:
        return f"<Inventory product={self.product_id} qty={self.quantity_on_hand}>"
