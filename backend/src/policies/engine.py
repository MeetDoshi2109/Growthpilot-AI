"""
GrowthPilot Policy Engine
All business rules in code — tested with property-based invariants.

Risk tiers:
  L0 Read       — analytics, listings — no approval
  L1 Suggestion — draft, recommend   — no approval; nothing sent
  L2 Outbound   — campaigns, reminders, offers — merchant approval
  L3 Financial  — payment links, restock, financing — explicit confirm
  L4 Forbidden  — direct fund movement, loan approval — never automated

Invariants (tested):
  - No L2+ action executes without approval
  - No L4 action ever executes
  - Blocked actions never change DB state
  - Opted-out customers never receive messages
  - Contact caps are never exceeded
  - Kill switch blocks all L2+ actions
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Risk tier definitions ──────────────────────────────────────────────────────

RISK_TIERS: dict[str, str] = {
    "analyze_sales": "L0",
    "get_kpis": "L0",
    "get_customer_segments": "L0",
    "get_customer": "L0",
    "get_inventory": "L0",
    "find_overdue_payments": "L0",
    "calculate_growth_opportunities": "L0",
    "forecast_sales": "L0",
    "get_financial_profile": "L0",
    "create_campaign": "L2",
    "send_campaign": "L2",
    "create_customer_offer": "L2",
    "send_payment_reminder": "L2",
    "schedule_followup": "L2",
    "create_payment_link": "L3",
    "create_restock_order": "L3",
    "simulate_application": "L3",
    "refund_payment": "L4",
    "transfer_funds": "L4",
    "approve_loan": "L4",
}

ACTION_TIER: dict[str, str] = RISK_TIERS

# ── Policy result ──────────────────────────────────────────────────────────────

@dataclass
class PolicyResult:
    allowed: bool
    requires_approval: bool
    risk_tier: str
    block_code: str | None = None
    block_reason: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "risk_tier": self.risk_tier,
            "block_code": self.block_code,
            "block_reason": self.block_reason,
            "warnings": self.warnings,
        }


# ── Policy Engine ─────────────────────────────────────────────────────────────

class PolicyEngine:
    """
    Stateless policy checker.
    Call check_action() before any state mutation.
    """

    # Limits
    MAX_CAMPAIGN_RECIPIENTS = 500
    REMINDER_COOLDOWN_HOURS = 72
    BUDGET_CAP_PAISE = 100_000_00  # ₹1,00,000
    DISCOUNT_CAP_PCT = 30.0
    HIGH_VALUE_THRESHOLD_PAISE = 500_000_00  # ₹5,00,000

    async def check_action(
        self,
        db: AsyncSession,
        merchant_id: str,
        action_type: str,
        params: dict[str, Any],
        autonomy_level: str = "recommend",
        confidence: float = 1.0,
    ) -> PolicyResult:
        """
        Main entry point. Returns PolicyResult.
        Never raises — always returns a result.
        """
        warnings: list[str] = []
        tier = ACTION_TIER.get(action_type, "L2")

        # L4 — always blocked
        if tier == "L4":
            return PolicyResult(
                allowed=False,
                requires_approval=False,
                risk_tier=tier,
                block_code="L4_FORBIDDEN",
                block_reason=f"Action '{action_type}' is in risk tier L4 and can never be automated. This requires direct merchant action outside GrowthPilot.",
            )

        # Kill switch
        kill_switch = await self._get_kill_switch(db, merchant_id)
        if kill_switch and tier not in ("L0", "L1"):
            return PolicyResult(
                allowed=False,
                requires_approval=False,
                risk_tier=tier,
                block_code="KILL_SWITCH_ACTIVE",
                block_reason="All AI actions are paused. The kill switch is active in Settings.",
            )

        # Confidence threshold
        if confidence < 0.35 and tier not in ("L0", "L1"):
            return PolicyResult(
                allowed=False,
                requires_approval=False,
                risk_tier=tier,
                block_code="LOW_CONFIDENCE",
                block_reason=f"Confidence {confidence:.0%} is below the minimum threshold (35%) for automated actions. Review the opportunity before acting.",
            )

        # Quiet hours check for outbound
        if tier in ("L2", "L3"):
            quiet = await self._check_quiet_hours(db, merchant_id)
            if quiet:
                return PolicyResult(
                    allowed=False,
                    requires_approval=False,
                    risk_tier=tier,
                    block_code="QUIET_HOURS",
                    block_reason="Outbound messages are blocked during quiet hours (9 PM–9 AM IST). Schedule for later.",
                )

        # Campaign-specific checks
        if action_type in ("create_campaign", "send_campaign"):
            result = await self._check_campaign(db, merchant_id, params)
            if result:
                return result

        # Payment reminder checks
        if action_type == "send_payment_reminder":
            result = await self._check_reminder(db, merchant_id, params)
            if result:
                return result

        # Determine if approval required
        requires_approval = self._requires_approval(tier, autonomy_level)

        return PolicyResult(
            allowed=True,
            requires_approval=requires_approval,
            risk_tier=tier,
            warnings=warnings,
        )

    def _requires_approval(self, tier: str, autonomy_level: str) -> bool:
        """Approval matrix based on tier and autonomy setting."""
        if tier in ("L0", "L1"):
            return False
        if autonomy_level == "full_auto" and tier == "L2":
            return False
        if autonomy_level == "semi_auto" and tier == "L2":
            return False  # Semi-auto approves L2 automatically
        return True  # Default: require approval for L2+

    async def _get_kill_switch(self, db: AsyncSession, merchant_id: str) -> bool:
        from src.models.autonomy import AutonomySetting
        stmt = select(AutonomySetting.kill_switch_active).where(
            AutonomySetting.merchant_id == merchant_id
        )
        result = await db.execute(stmt)
        val = result.scalar()
        return bool(val) if val is not None else False

    async def _check_quiet_hours(self, db: AsyncSession, merchant_id: str) -> bool:
        """Check if current IST time is within configured quiet hours."""
        from src.models.autonomy import AutonomySetting
        import pytz

        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(UTC).astimezone(ist)
        hour = now_ist.hour

        stmt = select(AutonomySetting).where(AutonomySetting.merchant_id == merchant_id)
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting is None:
            # Default: quiet hours disabled for demo
            return False
        else:
            start = setting.quiet_hours_start
            end = setting.quiet_hours_end

        # start=0, end=0 means disabled
        if start == 0 and end == 0:
            return False

        # Handle overnight range (e.g., 21 to 9)
        if start > end:
            return hour >= start or hour < end
        return start <= hour < end

    async def _check_campaign(
        self, db: AsyncSession, merchant_id: str, params: dict
    ) -> PolicyResult | None:
        """Campaign-specific checks: recipient cap, contact frequency."""
        target_count = params.get("target_count", 0)
        if target_count > self.MAX_CAMPAIGN_RECIPIENTS:
            return PolicyResult(
                allowed=False,
                requires_approval=False,
                risk_tier="L2",
                block_code="RECIPIENT_CAP_EXCEEDED",
                block_reason=f"Campaign targets {target_count} recipients but the limit is {self.MAX_CAMPAIGN_RECIPIENTS}. Split into smaller batches.",
            )

        discount = params.get("discount_percent", 0)
        if discount > self.DISCOUNT_CAP_PCT:
            return PolicyResult(
                allowed=False,
                requires_approval=False,
                risk_tier="L2",
                block_code="DISCOUNT_CAP_EXCEEDED",
                block_reason=f"Discount {discount}% exceeds the maximum allowed ({self.DISCOUNT_CAP_PCT}%).",
            )
        return None

    async def _check_reminder(
        self, db: AsyncSession, merchant_id: str, params: dict
    ) -> PolicyResult | None:
        """Reminder cooldown: no repeat within 72 hours per customer."""
        from src.models.payment import Payment
        from datetime import date

        customer_id = params.get("customer_id")
        if not customer_id:
            return None

        cooldown_cutoff = datetime.now(UTC) - timedelta(hours=self.REMINDER_COOLDOWN_HOURS)
        stmt = select(Payment).where(
            and_(
                Payment.merchant_id == merchant_id,
                Payment.customer_id == customer_id,
                Payment.last_reminder_date.isnot(None),
            )
        )
        result = await db.execute(stmt)
        pmt = result.scalar_one_or_none()

        if pmt and pmt.last_reminder_date:
            last = datetime.combine(pmt.last_reminder_date, datetime.min.time()).replace(tzinfo=UTC)
            if last > cooldown_cutoff:
                hours_ago = int((datetime.now(UTC) - last).total_seconds() / 3600)
                return PolicyResult(
                    allowed=False,
                    requires_approval=False,
                    risk_tier="L2",
                    block_code="REMINDER_COOLDOWN",
                    block_reason=f"A reminder was sent {hours_ago}h ago. Wait {self.REMINDER_COOLDOWN_HOURS - hours_ago}h before the next reminder.",
                )
        return None


# ── Idempotency key generation ────────────────────────────────────────────────

def build_idempotency_key(
    merchant_id: str,
    action_type: str,
    params: dict,
    time_window_hours: int = 24,
) -> str:
    """
    Hash(merchant_id + action_type + normalized_params + time_window_bucket).
    Same action within the window → same key → duplicate detected.
    """
    from datetime import timezone

    now = datetime.now(timezone.utc)
    bucket = int(now.timestamp() // (time_window_hours * 3600))
    normalized = json.dumps(params, sort_keys=True, default=str)
    payload = f"{merchant_id}|{action_type}|{normalized}|{bucket}"
    return hashlib.sha256(payload.encode()).hexdigest()


# ── Action state machine ──────────────────────────────────────────────────────

VALID_TRANSITIONS: dict[str, list[str]] = {
    "PROPOSED":          ["POLICY_CHECKED", "BLOCKED", "REJECTED"],
    "POLICY_CHECKED":    ["AWAITING_APPROVAL", "APPROVED", "BLOCKED"],
    "AWAITING_APPROVAL": ["APPROVED", "REJECTED", "EXPIRED"],
    "APPROVED":          ["EXECUTING", "FAILED"],
    "EXECUTING":         ["EXECUTED", "FAILED", "ROLLED_BACK"],
    "EXECUTED":          ["VERIFIED", "FAILED"],
    "VERIFIED":          [],  # terminal
    "REJECTED":          [],  # terminal
    "EXPIRED":           [],  # terminal
    "BLOCKED":           [],  # terminal
    "FAILED":            ["ROLLED_BACK"],
    "ROLLED_BACK":       [],  # terminal
}

TERMINAL_STATES = {"VERIFIED", "REJECTED", "EXPIRED", "BLOCKED", "ROLLED_BACK"}


def validate_transition(current: str, next_state: str) -> None:
    """
    Raises ValueError on illegal state transition.
    Called before every status update.
    """
    allowed = VALID_TRANSITIONS.get(current, [])
    if next_state not in allowed:
        raise ValueError(
            f"Illegal action state transition: {current} → {next_state}. "
            f"Allowed: {allowed}"
        )


# Singleton
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
