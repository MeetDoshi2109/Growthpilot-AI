"""Product model — catalog item."""
from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import SoftDeleteMixin, TimestampMixin, gen_uuid


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Price in paise
    unit_price_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_price_paise: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_products_merchant_category", "merchant_id", "category"),
        Index("ix_products_merchant_sku", "merchant_id", "sku"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} [{self.sku}]>"
