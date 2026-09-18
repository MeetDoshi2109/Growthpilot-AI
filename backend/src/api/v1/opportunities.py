"""Growth Opportunities API."""
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.models.opportunity import GrowthOpportunity
from src.models.base import gen_uuid
from src.opportunities.engine import compute_opportunities
from datetime import UTC, datetime

router = APIRouter()


async def _get_merchant_id(request: Request) -> str:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context")
    return merchant_id


@router.get("/")
async def list_opportunities(
    request: Request,
    refresh: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List active opportunities. Recomputes if refresh=true."""
    merchant_id = await _get_merchant_id(request)

    if refresh:
        # Expire old active opportunities
        from sqlalchemy import update
        await db.execute(
            __import__("sqlalchemy").text(
                f"UPDATE growth_opportunities SET status='expired' WHERE merchant_id='{merchant_id}' AND status='active'"
            )
        )
        opps_data = await compute_opportunities(db, merchant_id)
        for o in opps_data:
            opp = GrowthOpportunity(
                id=gen_uuid(),
                merchant_id=merchant_id,
                **{k: v for k, v in o.items() if k != "data_as_of"},
                data_as_of=o.get("data_as_of"),
            )
            db.add(opp)
        await db.flush()

    stmt = (
        select(GrowthOpportunity)
        .where(
            and_(
                GrowthOpportunity.merchant_id == merchant_id,
                GrowthOpportunity.status == "active",
            )
        )
        .order_by(GrowthOpportunity.priority.asc())
    )
    result = await db.execute(stmt)
    opps = result.scalars().all()

    # If none stored, compute and store
    if not opps:
        opps_data = await compute_opportunities(db, merchant_id)
        stored = []
        for o in opps_data:
            opp = GrowthOpportunity(
                id=gen_uuid(),
                merchant_id=merchant_id,
                opportunity_type=o["opportunity_type"],
                title=o["title"],
                description=o.get("description"),
                evidence=o.get("evidence"),
                affected_customers=o.get("affected_customers", 0),
                target_customer_ids=o.get("target_customer_ids"),
                estimated_impact_low_paise=o.get("estimated_impact_low_paise", 0),
                estimated_impact_base_paise=o.get("estimated_impact_base_paise", 0),
                estimated_impact_high_paise=o.get("estimated_impact_high_paise", 0),
                confidence=o.get("confidence", 0.5),
                priority=o.get("priority", 5),
                recommended_action=o.get("recommended_action"),
                action_params=o.get("action_params"),
                requires_approval=o.get("requires_approval", True),
                risk_notes=o.get("risk_notes"),
                explainability=o.get("explainability"),
                status="active",
                data_as_of=o.get("data_as_of"),
            )
            db.add(opp)
            stored.append(opp)
        await db.flush()
        opps = stored

    return {
        "opportunities": [_serialize_opp(o) for o in opps],
        "count": len(opps),
        "sandbox": True,
        "sandbox_label": "Sandbox · Synthetic Demo Data",
    }


@router.get("/{opp_id}")
async def get_opportunity(
    opp_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    stmt = select(GrowthOpportunity).where(
        and_(
            GrowthOpportunity.id == opp_id,
            GrowthOpportunity.merchant_id == merchant_id,
        )
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return _serialize_opp(opp)


def _serialize_opp(o: GrowthOpportunity) -> dict:
    exp = None
    if o.explainability:
        try:
            exp = json.loads(o.explainability)
        except Exception:
            exp = o.explainability
    return {
        "id": o.id,
        "opportunity_type": o.opportunity_type,
        "title": o.title,
        "description": o.description,
        "affected_customers": o.affected_customers,
        "estimated_impact_low_paise": o.estimated_impact_low_paise,
        "estimated_impact_base_paise": o.estimated_impact_base_paise,
        "estimated_impact_high_paise": o.estimated_impact_high_paise,
        "estimated_impact_low_rupees": round(o.estimated_impact_low_paise / 100, 2),
        "estimated_impact_base_rupees": round(o.estimated_impact_base_paise / 100, 2),
        "estimated_impact_high_rupees": round(o.estimated_impact_high_paise / 100, 2),
        "confidence": o.confidence,
        "priority": o.priority,
        "recommended_action": o.recommended_action,
        "requires_approval": o.requires_approval,
        "risk_notes": o.risk_notes,
        "status": o.status,
        "explainability": exp,
        "data_as_of": o.data_as_of.isoformat() if o.data_as_of else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }
