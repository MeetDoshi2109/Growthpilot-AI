"""Missions API — create, get, stream progress."""
import json
import asyncio
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.models.mission import Mission, MissionStep
from src.models.base import gen_uuid

router = APIRouter()


async def _get_merchant_id(request: Request) -> str:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context")
    return merchant_id


class CreateMissionRequest(BaseModel):
    goal: str
    title: str | None = None


DEMO_MISSION_PLAN = [
    {"step_number": 1, "title": "Analyze sales performance", "agent_name": "merchant_intelligence", "tool_name": "analyze_sales"},
    {"step_number": 2, "title": "Analyze customer segments", "agent_name": "customer", "tool_name": "get_customer_segments"},
    {"step_number": 3, "title": "Check inventory risks", "agent_name": "inventory", "tool_name": "get_inventory"},
    {"step_number": 4, "title": "Review overdue collections", "agent_name": "collections", "tool_name": "find_overdue_payments"},
    {"step_number": 5, "title": "Calculate growth opportunities", "agent_name": "growth", "tool_name": "calculate_growth_opportunities"},
    {"step_number": 6, "title": "Execute win-back campaign", "agent_name": "campaign", "tool_name": "send_campaign", "requires_approval": True},
    {"step_number": 7, "title": "Measure impact", "agent_name": "system", "tool_name": "verify_campaign"},
]


@router.post("/")
async def create_mission(
    body: CreateMissionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)

    title = body.title or "Grow my business"
    mission_id = gen_uuid()
    mission = Mission(
        id=mission_id,
        merchant_id=merchant_id,
        title=title,
        goal=body.goal,
        status="running",
        plan=json.dumps(DEMO_MISSION_PLAN),
        simulated=True,
        started_at=datetime.now(UTC),
    )
    db.add(mission)

    for step_def in DEMO_MISSION_PLAN:
        db.add(MissionStep(
            id=gen_uuid(),
            mission_id=mission_id,
            merchant_id=merchant_id,
            step_number=step_def["step_number"],
            title=step_def["title"],
            agent_name=step_def["agent_name"],
            tool_name=step_def.get("tool_name"),
            status="pending",
        ))

    await db.flush()
    return {
        "mission_id": mission_id,
        "title": title,
        "status": "running",
        "steps": DEMO_MISSION_PLAN,
        "simulated": True,
    }


@router.get("/{mission_id}")
async def get_mission(
    mission_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    stmt = select(Mission).where(
        and_(Mission.id == mission_id, Mission.merchant_id == merchant_id)
    )
    mission = (await db.execute(stmt)).scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    steps_stmt = select(MissionStep).where(
        MissionStep.mission_id == mission_id
    ).order_by(MissionStep.step_number)
    steps = (await db.execute(steps_stmt)).scalars().all()

    return {
        "mission_id": mission.id,
        "title": mission.title,
        "goal": mission.goal,
        "status": mission.status,
        "steps": [_serialize_step(s) for s in steps],
        "total_impact_paise": mission.total_impact_paise,
        "simulated": mission.simulated,
        "started_at": mission.started_at.isoformat() if mission.started_at else None,
        "completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
    }


@router.get("/{mission_id}/stream")
async def stream_mission_progress(
    mission_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """SSE stream of mission step progress."""
    merchant_id = await _get_merchant_id(request)

    async def event_generator():
        steps_stmt = select(MissionStep).where(
            MissionStep.mission_id == mission_id
        ).order_by(MissionStep.step_number)

        steps = (await db.execute(steps_stmt)).scalars().all()
        for step in steps:
            data = json.dumps({
                "step_number": step.step_number,
                "title": step.title,
                "status": step.status,
                "agent_name": step.agent_name,
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _serialize_step(s: MissionStep) -> dict:
    return {
        "id": s.id,
        "step_number": s.step_number,
        "title": s.title,
        "description": s.description,
        "agent_name": s.agent_name,
        "tool_name": s.tool_name,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "error_message": s.error_message,
    }
