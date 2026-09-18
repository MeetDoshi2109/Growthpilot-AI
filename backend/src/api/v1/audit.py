"""Audit Log API — list entries, verify chain."""
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.models.audit import AuditLog
from src.execution.audit import verify_audit_chain

router = APIRouter()


async def _get_merchant_id(request: Request) -> str:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context")
    return merchant_id


@router.get("/")
async def list_audit_log(
    request: Request,
    limit: int = Query(50, le=200),
    offset: int = 0,
    tool: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)

    stmt = (
        select(AuditLog)
        .where(AuditLog.merchant_id == merchant_id)
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
        .offset(offset)
    )
    if tool:
        stmt = stmt.where(AuditLog.tool == tool)

    result = await db.execute(stmt)
    entries = result.scalars().all()

    return {
        "entries": [_serialize(e) for e in entries],
        "count": len(entries),
        "limit": limit,
        "offset": offset,
    }


@router.get("/verify")
async def verify_chain(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify the hash chain integrity for the authenticated merchant."""
    merchant_id = await _get_merchant_id(request)
    result = await verify_audit_chain(db, merchant_id)
    return result


def _serialize(e: AuditLog) -> dict:
    import json
    inp = None
    if e.input_masked:
        try:
            inp = json.loads(e.input_masked)
        except Exception:
            inp = e.input_masked
    out = None
    if e.output_summary:
        try:
            out = json.loads(e.output_summary)
        except Exception:
            out = e.output_summary

    return {
        "id": e.id,
        "sequence_number": e.sequence_number,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "actor_type": e.actor_type,
        "actor_name": e.actor_name,
        "intent": e.intent,
        "tool": e.tool,
        "action_id": e.action_id,
        "input_masked": inp,
        "output_summary": out,
        "policy_result": e.policy_result,
        "approval_status": e.approval_status,
        "execution_status": e.execution_status,
        "verification_status": e.verification_status,
        "final_result": e.final_result,
        "simulated": e.simulated,
        "hash": e.hash[:12] + "..." if e.hash else None,
        "prev_hash": e.prev_hash[:12] + "..." if e.prev_hash else None,
    }
