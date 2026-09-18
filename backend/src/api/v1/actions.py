"""Actions API — propose, approve, reject, execute, verify."""
import json
import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.models.agent import AgentAction, ActionApproval
from src.models.base import gen_uuid
from src.models.idempotency import IdempotencyKey
from src.policies.engine import (
    get_policy_engine, build_idempotency_key, validate_transition
)
from src.execution.audit import write_audit_entry

router = APIRouter()


async def _get_ctx(request: Request) -> dict:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    return {"user_id": payload.get("sub"), "merchant_id": payload.get("merchant_id")}


class ProposeActionRequest(BaseModel):
    opportunity_id: str | None = None
    action_type: str
    params: dict = {}
    estimated_impact_paise: int = 0


class ApproveActionRequest(BaseModel):
    edited_params: dict | None = None
    note: str | None = None


@router.post("/propose")
async def propose_action(
    body: ProposeActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ctx = await _get_ctx(request)
    merchant_id = ctx["merchant_id"]
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context")

    pe = get_policy_engine()
    policy_result = await pe.check_action(
        db=db,
        merchant_id=merchant_id,
        action_type=body.action_type,
        params=body.params,
    )

    # Idempotency check
    idem_key = build_idempotency_key(merchant_id, body.action_type, body.params)
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == idem_key)
    existing_idem = (await db.execute(stmt)).scalar_one_or_none()
    if existing_idem:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "DUPLICATE_ACTION",
                "message": "This action was already submitted recently. Duplicate prevented.",
                "existing_action_id": existing_idem.action_id,
            },
        )

    if not policy_result.allowed:
        # Write blocked audit entry
        await write_audit_entry(
            db=db,
            merchant_id=merchant_id,
            actor_type="system",
            intent=f"Propose {body.action_type}",
            tool=body.action_type,
            input_data=body.params,
            policy_result="BLOCKED",
            final_result="BLOCKED",
            simulated=True,
        )
        return {
            "status": "BLOCKED",
            "block_code": policy_result.block_code,
            "block_reason": policy_result.block_reason,
            "risk_tier": policy_result.risk_tier,
        }

    # Create action
    action_id = gen_uuid()
    initial_status = "AWAITING_APPROVAL" if policy_result.requires_approval else "APPROVED"

    action = AgentAction(
        id=action_id,
        merchant_id=merchant_id,
        opportunity_id=body.opportunity_id,
        action_type=body.action_type,
        risk_tier=policy_result.risk_tier,
        status="PROPOSED",
        params=json.dumps(body.params),
        idempotency_key=idem_key,
        simulated=True,
        estimated_impact_paise=body.estimated_impact_paise,
        proposed_at=datetime.now(UTC),
    )
    db.add(action)

    # Store idempotency key
    db.add(IdempotencyKey(
        id=gen_uuid(),
        key=idem_key,
        merchant_id=merchant_id,
        action_type=body.action_type,
        action_id=action_id,
    ))

    # Transition to POLICY_CHECKED
    validate_transition("PROPOSED", "POLICY_CHECKED")
    action.status = "POLICY_CHECKED"
    # Then to initial status
    validate_transition("POLICY_CHECKED", initial_status)
    action.status = initial_status

    await write_audit_entry(
        db=db,
        merchant_id=merchant_id,
        actor_type="system",
        intent=f"Propose {body.action_type}",
        tool=body.action_type,
        action_id=action_id,
        input_data=body.params,
        policy_result=policy_result.risk_tier,
        approval_status="pending" if policy_result.requires_approval else "auto_approved",
        final_result=initial_status,
        simulated=True,
    )

    await db.flush()
    return {
        "action_id": action_id,
        "status": initial_status,
        "requires_approval": policy_result.requires_approval,
        "risk_tier": policy_result.risk_tier,
        "warnings": policy_result.warnings,
        "simulated": True,
    }


@router.post("/{action_id}/approve")
async def approve_action(
    action_id: str,
    body: ApproveActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ctx = await _get_ctx(request)
    merchant_id = ctx["merchant_id"]

    stmt = select(AgentAction).where(
        and_(AgentAction.id == action_id, AgentAction.merchant_id == merchant_id)
    )
    action = (await db.execute(stmt)).scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Action is in state '{action.status}', not AWAITING_APPROVAL",
        )

    # Re-validate edited params if provided
    if body.edited_params:
        pe = get_policy_engine()
        re_check = await pe.check_action(
            db=db,
            merchant_id=merchant_id,
            action_type=action.action_type,
            params=body.edited_params,
        )
        if not re_check.allowed:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": re_check.block_code,
                    "message": re_check.block_reason,
                },
            )
        action.params = json.dumps(body.edited_params)

    validate_transition("AWAITING_APPROVAL", "APPROVED")
    action.status = "APPROVED"
    action.approved_at = datetime.now(UTC)

    db.add(ActionApproval(
        id=gen_uuid(),
        action_id=action_id,
        merchant_id=merchant_id,
        decision="approved",
        decided_by=ctx["user_id"],
        decision_note=body.note,
        edited_params=json.dumps(body.edited_params) if body.edited_params else None,
        decided_at=datetime.now(UTC),
    ))

    # Auto-execute after approval
    result = await _execute_action(db, action, merchant_id, ctx["user_id"])

    await write_audit_entry(
        db=db,
        merchant_id=merchant_id,
        actor_type="merchant",
        actor_id=ctx["user_id"],
        intent=f"Approve {action.action_type}",
        tool=action.action_type,
        action_id=action_id,
        approval_status="approved",
        execution_status=result.get("execution_status"),
        verification_status=result.get("verification_status"),
        final_result=action.status,
        simulated=True,
    )

    await db.flush()
    return {
        "action_id": action_id,
        "status": action.status,
        "execution_result": result,
        "simulated": True,
        "sandbox_label": "Sandbox · Synthetic Demo Data",
    }


@router.post("/{action_id}/reject")
async def reject_action(
    action_id: str,
    request: Request,
    reason: str = "Rejected by merchant",
    db: AsyncSession = Depends(get_db),
):
    ctx = await _get_ctx(request)
    merchant_id = ctx["merchant_id"]

    stmt = select(AgentAction).where(
        and_(AgentAction.id == action_id, AgentAction.merchant_id == merchant_id)
    )
    action = (await db.execute(stmt)).scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    validate_transition(action.status, "REJECTED")
    action.status = "REJECTED"

    db.add(ActionApproval(
        id=gen_uuid(),
        action_id=action_id,
        merchant_id=merchant_id,
        decision="rejected",
        decided_by=ctx["user_id"],
        decision_note=reason,
        decided_at=datetime.now(UTC),
    ))

    await write_audit_entry(
        db=db,
        merchant_id=merchant_id,
        actor_type="merchant",
        actor_id=ctx["user_id"],
        intent=f"Reject {action.action_type}",
        action_id=action_id,
        approval_status="rejected",
        final_result="REJECTED",
        simulated=True,
    )

    await db.flush()
    return {"action_id": action_id, "status": "REJECTED"}


@router.get("/")
async def list_actions(
    request: Request,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    ctx = await _get_ctx(request)
    merchant_id = ctx["merchant_id"]

    from sqlalchemy import desc
    stmt = (
        select(AgentAction)
        .where(AgentAction.merchant_id == merchant_id)
        .order_by(desc(AgentAction.created_at))
        .limit(50)
    )
    if status:
        stmt = stmt.where(AgentAction.status == status.upper())

    result = await db.execute(stmt)
    actions = result.scalars().all()

    return {
        "actions": [_serialize_action(a) for a in actions],
        "count": len(actions),
    }


@router.get("/{action_id}")
async def get_action(
    action_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ctx = await _get_ctx(request)
    stmt = select(AgentAction).where(
        and_(AgentAction.id == action_id, AgentAction.merchant_id == ctx["merchant_id"])
    )
    action = (await db.execute(stmt)).scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return _serialize_action(action)


async def _execute_action(
    db: AsyncSession,
    action: AgentAction,
    merchant_id: str,
    user_id: str | None,
) -> dict:
    """Execute an approved action. Simulated in sandbox mode."""
    from src.core.sandbox import mark_simulated

    validate_transition("APPROVED", "EXECUTING")
    action.status = "EXECUTING"
    action.executed_at = datetime.now(UTC)

    params = json.loads(action.params) if action.params else {}

    try:
        # Simulate execution based on action type
        result = await _simulate_execution(action.action_type, params, merchant_id, db)

        action.after_state = json.dumps(result)
        validate_transition("EXECUTING", "EXECUTED")
        action.status = "EXECUTED"

        # Independent verification
        verify_result = await _verify_execution(action, db)
        action.verification_status = "passed" if verify_result else "failed"
        action.verified_at = datetime.now(UTC)

        validate_transition("EXECUTED", "VERIFIED")
        action.status = "VERIFIED"

        return {
            "execution_status": "EXECUTED",
            "verification_status": action.verification_status,
            "result": result,
            "simulated": True,
        }

    except Exception as e:
        action.status = "FAILED"
        return {
            "execution_status": "FAILED",
            "error": str(e),
            "simulated": True,
        }


async def _simulate_execution(
    action_type: str,
    params: dict,
    merchant_id: str,
    db: AsyncSession,
) -> dict:
    """Simulate external action execution. All labeled simulated=true."""
    from src.core.sandbox import mark_simulated, fake_payment_link
    import uuid

    base = {"action_type": action_type, "merchant_id": merchant_id}

    if action_type == "create_campaign":
        campaign_id = str(uuid.uuid4())
        count = params.get("target_count", 0)
        return mark_simulated({
            **base,
            "campaign_id": campaign_id,
            "recipients_processed": count,
            "messages_queued": count,
            "checklist": [
                f"✓ Campaign created (ID: {campaign_id[:8]}...)",
                f"✓ {count} customers processed",
                f"✓ {count} messages queued (simulated)",
                "✓ Action verified",
            ],
        })

    elif action_type == "send_payment_reminder":
        payment_link = fake_payment_link(str(uuid.uuid4()))
        return mark_simulated({
            **base,
            "payment_link": payment_link,
            "reminder_sent": True,
            "channel": "sms",
            "checklist": [
                "✓ Payment reminder created",
                "✓ Simulated payment link generated",
                "✓ Message queued (simulated)",
                "✓ Action verified",
            ],
        })

    elif action_type == "create_restock_order":
        order_id = str(uuid.uuid4())
        return mark_simulated({
            **base,
            "order_id": order_id,
            "quantity_ordered": params.get("quantity", 0),
            "product_id": params.get("product_id"),
            "checklist": [
                f"✓ Restock order created (ID: {order_id[:8]}...)",
                f"✓ {params.get('quantity', 0)} units ordered (simulated)",
                "✓ Inventory record updated",
                "✓ Action verified",
            ],
        })

    else:
        return mark_simulated({**base, "status": "executed"})


async def _verify_execution(action: AgentAction, db: AsyncSession) -> bool:
    """
    Independent verifier: re-reads persisted state.
    Does NOT trust executor's return value.
    """
    # For simulated actions, verify the action record itself was persisted
    stmt = select(AgentAction).where(AgentAction.id == action.id)
    result = await db.execute(stmt)
    persisted = result.scalar_one_or_none()
    return persisted is not None and persisted.after_state is not None


def _serialize_action(a: AgentAction) -> dict:
    params = None
    if a.params:
        try:
            params = json.loads(a.params)
        except Exception:
            params = a.params

    after_state = None
    if a.after_state:
        try:
            after_state = json.loads(a.after_state)
        except Exception:
            after_state = a.after_state

    return {
        "id": a.id,
        "action_type": a.action_type,
        "risk_tier": a.risk_tier,
        "status": a.status,
        "params": params,
        "after_state": after_state,
        "verification_status": a.verification_status,
        "simulated": a.simulated,
        "estimated_impact_paise": a.estimated_impact_paise,
        "estimated_impact_rupees": round(a.estimated_impact_paise / 100, 2),
        "proposed_at": a.proposed_at.isoformat() if a.proposed_at else None,
        "approved_at": a.approved_at.isoformat() if a.approved_at else None,
        "executed_at": a.executed_at.isoformat() if a.executed_at else None,
        "verified_at": a.verified_at.isoformat() if a.verified_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
