"""Dashboard API — KPIs, revenue trend, opportunities summary."""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.analytics.engine import (
    get_kpis, get_revenue_summary, get_inactive_customers,
    get_inventory_risks, get_overdue_payments, get_retention_metrics,
    get_revenue_change_attribution,
)

router = APIRouter()


async def _get_merchant_id(request: Request) -> str:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context in token")
    return merchant_id


@router.get("/kpis")
async def get_dashboard_kpis(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_kpis(db, merchant_id)


@router.get("/revenue")
async def get_revenue(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_revenue_summary(db, merchant_id, days=days)


@router.get("/attribution")
async def get_attribution(
    request: Request,
    days: int = 14,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_revenue_change_attribution(db, merchant_id, days=days)


@router.get("/retention")
async def get_retention(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_retention_metrics(db, merchant_id, days=days)


@router.get("/inventory-risks")
async def get_inv_risks(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_inventory_risks(db, merchant_id)


@router.get("/inactive-customers")
async def get_inactive(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_inactive_customers(db, merchant_id)


@router.get("/overdue-payments")
async def get_overdue(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    merchant_id = await _get_merchant_id(request)
    return await get_overdue_payments(db, merchant_id)
