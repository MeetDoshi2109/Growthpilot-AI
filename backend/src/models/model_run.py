"""ModelRun model — ML model training run metadata."""
from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class ModelRun(Base, TimestampMixin):
    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    train_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    train_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metrics: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    pr_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_mape: Mapped[float | None] = mapped_column(Float, nullable=True)

    train_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    val_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_model_runs_name_version", "model_name", "model_version"),
        Index("ix_model_runs_merchant", "merchant_id"),
    )
