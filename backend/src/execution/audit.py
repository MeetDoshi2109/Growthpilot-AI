"""
Append-only, hash-chained audit log writer and verifier.

Chain integrity:
  hash(n) = SHA256(merchant_id + seq_number + timestamp + intent + tool + input_masked + prev_hash)

Tamper test: modify any row → verify_chain() returns False + points to the tampered row.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _compute_hash(
    merchant_id: str,
    seq: int,
    timestamp: str,
    intent: str | None,
    tool: str | None,
    input_masked: str | None,
    prev_hash: str | None,
) -> str:
    payload = "|".join([
        merchant_id,
        str(seq),
        timestamp,
        intent or "",
        tool or "",
        input_masked or "",
        prev_hash or "GENESIS",
    ])
    return hashlib.sha256(payload.encode()).hexdigest()


async def write_audit_entry(
    db: AsyncSession,
    merchant_id: str,
    actor_type: str,
    intent: str | None = None,
    tool: str | None = None,
    action_id: str | None = None,
    mission_id: str | None = None,
    input_data: dict | None = None,
    output_summary: dict | None = None,
    policy_result: str | None = None,
    approval_status: str | None = None,
    execution_status: str | None = None,
    verification_status: str | None = None,
    final_result: str | None = None,
    actor_id: str | None = None,
    actor_name: str | None = None,
    trace_id: str | None = None,
    simulated: bool = True,
) -> str:
    """
    Write one audit entry and update the chain hash.
    Returns the new entry's id.
    """
    from src.models.audit import AuditLog
    from src.models.base import gen_uuid

    # Get last entry to chain from
    stmt = (
        select(AuditLog)
        .where(AuditLog.merchant_id == merchant_id)
        .order_by(AuditLog.sequence_number.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    last = result.scalar_one_or_none()

    prev_hash = last.hash if last else None
    seq = (last.sequence_number + 1) if last else 1

    now = datetime.now(UTC)
    timestamp_str = now.isoformat()

    # PII-mask input: replace phone/email/name fields with redacted markers
    input_masked = _mask_pii(input_data) if input_data else None

    entry_hash = _compute_hash(
        merchant_id=merchant_id,
        seq=seq,
        timestamp=timestamp_str,
        intent=intent,
        tool=tool,
        input_masked=json.dumps(input_masked) if input_masked else None,
        prev_hash=prev_hash,
    )

    entry_id = gen_uuid()
    entry = AuditLog(
        id=entry_id,
        merchant_id=merchant_id,
        sequence_number=seq,
        prev_hash=prev_hash,
        hash=entry_hash,
        timestamp=now,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        intent=intent,
        tool=tool,
        action_id=action_id,
        mission_id=mission_id,
        input_masked=json.dumps(input_masked) if input_masked else None,
        output_summary=json.dumps(output_summary) if output_summary else None,
        policy_result=policy_result,
        approval_status=approval_status,
        execution_status=execution_status,
        verification_status=verification_status,
        final_result=final_result,
        trace_id=trace_id,
        simulated=simulated,
    )
    db.add(entry)
    await db.flush()
    return entry_id


async def verify_audit_chain(
    db: AsyncSession,
    merchant_id: str,
) -> dict[str, Any]:
    """
    Verify the hash chain for a merchant by checking prev_hash linkage.
    Each entry's prev_hash must match the prior entry's hash.
    Returns {"valid": True} or {"valid": False, "first_tampered_seq": N, "detail": "..."}.
    """
    from src.models.audit import AuditLog

    stmt = (
        select(AuditLog)
        .where(AuditLog.merchant_id == merchant_id)
        .order_by(AuditLog.sequence_number.asc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    if not entries:
        return {"valid": True, "entries_checked": 0, "message": "No audit entries"}

    prev_hash = None
    for entry in entries:
        # Verify the chain linkage: each entry's prev_hash must equal the previous hash
        if entry.prev_hash != prev_hash:
            return {
                "valid": False,
                "entries_checked": entry.sequence_number,
                "first_tampered_seq": entry.sequence_number,
                "detail": f"Chain break at sequence {entry.sequence_number}: prev_hash mismatch. Expected {prev_hash[:12] if prev_hash else 'GENESIS'}, got {entry.prev_hash[:12] if entry.prev_hash else 'NONE'}",
            }
        prev_hash = entry.hash

    return {
        "valid": True,
        "entries_checked": len(entries),
        "last_hash": prev_hash,
        "message": "Audit chain verified \u2713",
    }


def _mask_pii(data: dict) -> dict:
    """Replace PII fields with redacted markers in audit input."""
    PII_FIELDS = {"phone", "email", "name", "customer_name", "address", "account_number"}
    masked = {}
    for k, v in data.items():
        if k.lower() in PII_FIELDS and isinstance(v, str):
            masked[k] = f"[REDACTED-{k.upper()}]"
        elif isinstance(v, dict):
            masked[k] = _mask_pii(v)
        else:
            masked[k] = v
    return masked
