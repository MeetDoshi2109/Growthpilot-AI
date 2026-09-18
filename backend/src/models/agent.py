"""AgentTask, AgentAction, and ActionApproval models."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.models.base import TimestampMixin, gen_uuid


class AgentTask(Base, TimestampMixin):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | running | completed | failed | cancelled

    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    __table_args__ = (
        Index("ix_agent_tasks_merchant_status", "merchant_id", "status"),
        Index("ix_agent_tasks_mission", "mission_id"),
    )


class AgentAction(Base, TimestampMixin):
    __tablename__ = "agent_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Action classification
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # create_campaign | send_campaign | create_payment_link | send_payment_reminder
    # create_restock_order | schedule_followup | create_customer_offer | simulate_application

    risk_tier: Mapped[str] = mapped_column(String(10), nullable=False, default="L2")
    # L0 | L1 | L2 | L3 | L4

    # Action lifecycle state machine
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROPOSED")
    # PROPOSED | POLICY_CHECKED | AWAITING_APPROVAL | APPROVED | EXECUTING
    # EXECUTED | VERIFIED | REJECTED | EXPIRED | BLOCKED | FAILED | ROLLED_BACK

    # Parameters (Pydantic-validated, PII-masked)
    params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Policy check result
    policy_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    policy_block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_block_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Execution
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    affected_entities: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    # Verification
    verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # passed | failed | skipped
    verification_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit reference
    audit_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Timestamps
    proposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Impact tracking
    estimated_impact_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_impact_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_agent_actions_merchant_status", "merchant_id", "status"),
        Index("ix_agent_actions_merchant_type", "merchant_id", "action_type"),
        Index("ix_agent_actions_idempotency", "idempotency_key"),
    )

    def __repr__(self) -> str:
        return f"<AgentAction {self.action_type} [{self.status}]>"


class ActionApproval(Base, TimestampMixin):
    __tablename__ = "action_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    action_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    # approved | rejected | expired

    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)  # user_id
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Edited parameters (if merchant changed params before approving)
    edited_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_action_approvals_action", "action_id"),
        Index("ix_action_approvals_merchant", "merchant_id"),
    )
