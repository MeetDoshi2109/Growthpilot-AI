"""User model — authentication and roles."""
from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.base import SoftDeleteMixin, TimestampMixin, gen_uuid


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="merchant_owner"
    )  # merchant_owner | merchant_staff | admin_readonly
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    merchant_users: Mapped[list["MerchantUser"]] = relationship(
        "MerchantUser", back_populates="user", lazy="selectin"
    )

    __table_args__ = (Index("ix_users_email_active", "email", "is_active"),)

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


class MerchantUser(Base, TimestampMixin):
    """Association between users and merchants (multi-merchant support)."""
    __tablename__ = "merchant_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="merchant_owner")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="merchant_users")

    __table_args__ = (
        Index("ix_merchant_users_user_merchant", "user_id", "merchant_id", unique=True),
    )
