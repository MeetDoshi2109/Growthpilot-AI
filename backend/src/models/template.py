"""MessageTemplate model — DLT-style registered message templates."""
from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class MessageTemplate(Base, TimestampMixin):
    __tablename__ = "message_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    # None = global template available to all merchants

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # winback | retention | payment_reminder | restock | promotion

    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="sms")
    # sms | whatsapp | email | push

    # Template body with {placeholder} variables
    body: Mapped[str] = mapped_column(Text, nullable=False)

    has_opt_out_line: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_length: Mapped[int] = mapped_column(Integer, nullable=False, default=160)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    # en | hi | hinglish

    __table_args__ = (
        Index("ix_message_templates_type_channel", "template_type", "channel"),
    )
