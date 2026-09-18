"""
GrowthPilot Analytics Engine
All metrics are computed deterministically from raw DB data.
The LLM may only phrase results — never compute them.

Key rule: if a metric cannot be computed, return {"value": None, "unavailable": True, "reason": "..."}
Never return a guess or zero for an unavailable metric.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd
import numpy as np
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _paise_to_rupees(paise: int | float | None) -> float | None:
    if paise is None:
        return None
    return round(paise / 100, 2)


def _unavailable(reason: str) -> dict:
    return {"value": None, "unavailable": True, "reason": reason}


def _require_min_samples(df: pd.DataFrame, n: int, reason: str) -> dict | None:
    """Return unavailable dict if df has fewer than n rows, else None."""
    if len(df) < n:
        return _unavailable(reason)
    return None


# ── Revenue metrics ───────────────────────────────────────────────────────────

async def get_revenue_summary(
    db: AsyncSession,
    merchant_id: str,
    days: int = 30,
) -> dict[str, Any]:
    """
    Returns daily/weekly/monthly revenue, GMV, transaction count,
    AOV, growth %, success rate.
    """
    from src.models.transaction import Transaction

    now = datetime.now(UTC)
    window_start = now - timedelta(days=days)
    prior_start = now - timedelta(days=days * 2)

    # Fetch transactions for current + prior window
    stmt = select(Transaction).where(
        and_(
            Transaction.merchant_id == merchant_id,
            Transaction.transaction_date >= prior_start,
        )
    )
    result = await db.execute(stmt)
    txns = result.scalars().all()

    if not txns:
        return _unavailable("No transactions found for merchant in this window")

    df = pd.DataFrame([{
        "date": t.transaction_date.date() if hasattr(t.transaction_date, "date") else t.transaction_date,
        "amount_paise": t.amount_paise,
        "status": t.payment_status,
        "customer_id": t.customer_id,
    } for t in txns])

    df["date"] = pd.to_datetime(df["date"])
    current = df[df["date"] >= pd.Timestamp(window_start.date())]
    prior = df[df["date"] < pd.Timestamp(window_start.date())]

    cur_success = current[current["status"] == "success"]
    prior_success = prior[prior["status"] == "success"]

    cur_gmv = int(cur_success["amount_paise"].sum()) if len(cur_success) > 0 else 0
    prior_gmv = int(prior_success["amount_paise"].sum()) if len(prior_success) > 0 else 0

    growth_pct = None
    if prior_gmv > 0:
        growth_pct = round((cur_gmv - prior_gmv) / prior_gmv * 100, 2)

    cur_txn_count = len(cur_success)
    aov = round(cur_gmv / cur_txn_count) if cur_txn_count > 0 else 0

    total_attempts = len(current)
    success_rate = round(cur_txn_count / total_attempts * 100, 1) if total_attempts > 0 else None

    # Daily revenue for trend
    daily = cur_success.groupby(cur_success["date"].dt.date)["amount_paise"].sum()
    daily_list = [
        {"date": str(d), "revenue_paise": int(v)}
        for d, v in daily.items()
    ]

    return {
        "period_days": days,
        "gmv_paise": cur_gmv,
        "gmv_rupees": _paise_to_rupees(cur_gmv),
        "prior_gmv_paise": prior_gmv,
        "transaction_count": cur_txn_count,
        "aov_paise": aov,
        "aov_rupees": _paise_to_rupees(aov),
        "growth_pct": growth_pct,
        "payment_success_rate": success_rate,
        "daily_revenue": daily_list,
        "data_as_of": now.isoformat(),
    }


async def get_kpis(db: AsyncSession, merchant_id: str) -> dict[str, Any]:
    """Dashboard KPI cards: Revenue, Transactions, Customers, Growth, Collections."""
    rev_30 = await get_revenue_summary(db, merchant_id, days=30)
    rev_7 = await get_revenue_summary(db, merchant_id, days=7)

    from src.models.payment import Payment
    stmt = select(
        func.count(Payment.id).label("overdue_count"),
        func.sum(Payment.amount_paise).label("overdue_paise"),
    ).where(
        and_(
            Payment.merchant_id == merchant_id,
            Payment.status == "overdue",
        )
    )
    result = await db.execute(stmt)
    row = result.one()
    overdue_count = row.overdue_count or 0
    overdue_paise = row.overdue_paise or 0

    from src.models.customer import Customer
    stmt2 = select(func.count(Customer.id)).where(
        Customer.merchant_id == merchant_id
    )
    total_customers = (await db.execute(stmt2)).scalar() or 0

    return {
        "revenue_30d": rev_30,
        "revenue_7d": rev_7,
        "total_customers": total_customers,
        "overdue_count": overdue_count,
        "overdue_paise": overdue_paise,
        "overdue_rupees": _paise_to_rupees(overdue_paise),
        "data_as_of": datetime.now(UTC).isoformat(),
    }


# ── Customer analytics ────────────────────────────────────────────────────────

async def get_inactive_customers(
    db: AsyncSession,
    merchant_id: str,
    cadence_multiplier: float = 2.0,
) -> dict[str, Any]:
    """
    Returns customers inactive relative to their OWN cadence.
    Inactive = days_since_last_purchase > cadence_multiplier × median_cadence.
    NOT a fixed 30-day window.
    """
    from src.models.customer import Customer

    stmt = select(Customer).where(
        and_(
            Customer.merchant_id == merchant_id,
            Customer.median_purchase_cadence_days.isnot(None),
            Customer.days_since_last_purchase.isnot(None),
            Customer.total_orders >= 2,
        )
    )
    result = await db.execute(stmt)
    customers = result.scalars().all()

    if not customers:
        return _unavailable("No customers with sufficient purchase history")

    inactive = []
    for c in customers:
        threshold = c.median_purchase_cadence_days * cadence_multiplier
        if c.days_since_last_purchase > threshold:
            inactive.append({
                "customer_id": c.id,
                "name": c.name,
                "days_since_last_purchase": c.days_since_last_purchase,
                "median_cadence_days": c.median_purchase_cadence_days,
                "threshold_days": round(threshold, 1),
                "overdue_by_days": round(c.days_since_last_purchase - threshold, 1),
                "avg_order_value_paise": c.avg_order_value_paise,
                "total_orders": c.total_orders,
                "sms_consent": c.sms_consent,
            })

    avg_aov = int(np.mean([i["avg_order_value_paise"] for i in inactive])) if inactive else 0

    return {
        "inactive_count": len(inactive),
        "total_eligible": len(customers),
        "avg_aov_paise": avg_aov,
        "avg_aov_rupees": _paise_to_rupees(avg_aov),
        "customers": inactive[:200],  # cap for API response
        "cadence_multiplier_used": cadence_multiplier,
        "data_as_of": datetime.now(UTC).isoformat(),
    }


async def get_revenue_change_attribution(
    db: AsyncSession,
    merchant_id: str,
    days: int = 14,
) -> dict[str, Any]:
    """
    Decompose revenue change into:
    volume_effect, aov_effect, repeat_customer_effect,
    new_customer_effect, payment_failure_effect.

    Returns computed decomposition — NOT an LLM opinion.
    """
    from src.models.transaction import Transaction
    from src.models.order import Order

    now = datetime.now(UTC)
    cur_start = now - timedelta(days=days)
    prior_start = now - timedelta(days=days * 2)

    stmt = select(Transaction).where(
        and_(
            Transaction.merchant_id == merchant_id,
            Transaction.transaction_date >= prior_start,
        )
    )
    result = await db.execute(stmt)
    txns = result.scalars().all()

    if len(txns) < 5:
        return _unavailable("Insufficient transaction data for attribution (< 5 transactions)")

    df = pd.DataFrame([{
        "date": t.transaction_date,
        "amount_paise": t.amount_paise,
        "status": t.payment_status,
        "customer_id": t.customer_id,
    } for t in txns])

    df["date"] = pd.to_datetime(df["date"], utc=True)
    # Normalize comparison timestamps to UTC-aware
    cur_start_ts = pd.Timestamp(cur_start).tz_localize("UTC") if pd.Timestamp(cur_start).tzinfo is None else pd.Timestamp(cur_start)
    cur_df = df[df["date"] >= cur_start_ts]
    prior_df = df[df["date"] < cur_start_ts]

    def _metrics(d: pd.DataFrame) -> dict:
        success = d[d["status"] == "success"]
        rev = int(success["amount_paise"].sum())
        count = len(success)
        aov = round(rev / count) if count > 0 else 0
        unique_customers = success["customer_id"].nunique()
        failed = len(d[d["status"] == "failed"])
        return {
            "revenue": rev, "count": count, "aov": aov,
            "unique_customers": unique_customers, "failed": failed,
        }

    cur_m = _metrics(cur_df)
    prior_m = _metrics(prior_df)

    # Volume effect: change in transaction count × prior AOV
    volume_effect = (cur_m["count"] - prior_m["count"]) * prior_m["aov"]
    # AOV effect: change in AOV × current count
    aov_effect = (cur_m["aov"] - prior_m["aov"]) * cur_m["count"]
    # Customer mix effect: change in unique customers × AOV
    customer_mix_effect = (cur_m["unique_customers"] - prior_m["unique_customers"]) * cur_m["aov"]
    # Payment failure effect: lost revenue from failures
    failure_rate_change = (
        cur_m["failed"] / max(1, len(cur_df)) - prior_m["failed"] / max(1, len(prior_df))
    )
    payment_failure_effect = -int(failure_rate_change * cur_m["revenue"])

    total_change = cur_m["revenue"] - prior_m["revenue"]
    change_pct = round(total_change / prior_m["revenue"] * 100, 1) if prior_m["revenue"] > 0 else None

    return {
        "current_revenue_paise": cur_m["revenue"],
        "prior_revenue_paise": prior_m["revenue"],
        "total_change_paise": total_change,
        "change_pct": change_pct,
        "period_days": days,
        "attribution": {
            "volume_effect_paise": volume_effect,
            "aov_effect_paise": aov_effect,
            "customer_mix_effect_paise": customer_mix_effect,
            "payment_failure_effect_paise": payment_failure_effect,
        },
        "primary_driver": _primary_driver(
            volume_effect, aov_effect, customer_mix_effect, payment_failure_effect
        ),
        "data_as_of": datetime.now(UTC).isoformat(),
    }


def _primary_driver(
    volume: int, aov: int, customer_mix: int, failure: int
) -> str:
    effects = {
        "volume_change": abs(volume),
        "aov_change": abs(aov),
        "customer_mix_change": abs(customer_mix),
        "payment_failures": abs(failure),
    }
    return max(effects, key=effects.get)


# ── Inventory analytics ───────────────────────────────────────────────────────

async def get_inventory_risks(
    db: AsyncSession,
    merchant_id: str,
) -> dict[str, Any]:
    """Returns products at risk of stockout, ordered by urgency."""
    from src.models.inventory import InventoryItem
    from src.models.product import Product

    stmt = (
        select(InventoryItem, Product)
        .join(Product, InventoryItem.product_id == Product.id)
        .where(
            and_(
                InventoryItem.merchant_id == merchant_id,
                Product.is_active == True,  # noqa: E712
            )
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    risks = []
    for inv, prod in rows:
        if inv.avg_daily_demand and inv.avg_daily_demand > 0:
            days_until = inv.quantity_on_hand / inv.avg_daily_demand
        else:
            days_until = 999.0

        status = "ok"
        if days_until <= inv.supplier_lead_time_days + inv.safety_stock_days:
            status = "STOCKOUT_RISK"
        elif days_until <= (inv.supplier_lead_time_days + inv.safety_stock_days) * 2:
            status = "LOW_STOCK"

        lead_time = inv.supplier_lead_time_days
        safety = inv.safety_stock_days
        daily = inv.avg_daily_demand or 0
        restock_qty = max(
            0,
            int(np.ceil(daily * (lead_time + safety) - inv.quantity_on_hand))
        )
        revenue_at_risk = int(max(0, daily * (lead_time + safety) - inv.quantity_on_hand) * prod.unit_price_paise)

        risks.append({
            "product_id": prod.id,
            "product_name": prod.name,
            "category": prod.category,
            "quantity_on_hand": inv.quantity_on_hand,
            "avg_daily_demand": round(daily, 2),
            "days_until_stockout": round(days_until, 1),
            "status": status,
            "restock_quantity": max(0, restock_qty),
            "revenue_at_risk_paise": revenue_at_risk,
            "revenue_at_risk_rupees": _paise_to_rupees(revenue_at_risk),
            "unit_price_paise": prod.unit_price_paise,
            "supplier_lead_time_days": lead_time,
        })

    risks.sort(key=lambda x: x["days_until_stockout"])
    critical = [r for r in risks if r["status"] == "STOCKOUT_RISK"]
    low = [r for r in risks if r["status"] == "LOW_STOCK"]

    return {
        "total_products": len(risks),
        "stockout_risk_count": len(critical),
        "low_stock_count": len(low),
        "risks": risks,
        "data_as_of": datetime.now(UTC).isoformat(),
    }


# ── Overdue payments ──────────────────────────────────────────────────────────

async def get_overdue_payments(
    db: AsyncSession,
    merchant_id: str,
) -> dict[str, Any]:
    """Returns overdue payments with aging buckets and recovery probability."""
    from src.models.payment import Payment
    from src.models.customer import Customer

    stmt = (
        select(Payment, Customer)
        .outerjoin(Customer, Payment.customer_id == Customer.id)
        .where(
            and_(
                Payment.merchant_id == merchant_id,
                Payment.status == "overdue",
            )
        )
        .order_by(Payment.days_overdue.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    payments = []
    total_paise = 0
    for pmt, cust in rows:
        # Recovery probability: heuristic based on days overdue + payer history
        recovery_prob = _recovery_probability(
            days_overdue=pmt.days_overdue,
            failed_count=cust.failed_payment_count if cust else 0,
        )
        aging_bucket = _aging_bucket(pmt.days_overdue)

        payments.append({
            "payment_id": pmt.id,
            "customer_id": pmt.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "amount_paise": pmt.amount_paise,
            "amount_rupees": _paise_to_rupees(pmt.amount_paise),
            "days_overdue": pmt.days_overdue,
            "due_date": str(pmt.due_date),
            "aging_bucket": aging_bucket,
            "recovery_probability": recovery_prob,
            "expected_recovery_paise": int(pmt.amount_paise * recovery_prob),
            "reminder_sent_count": pmt.reminder_sent_count,
        })
        total_paise += pmt.amount_paise

    total_expected_recovery = sum(
        int(p["amount_paise"] * p["recovery_probability"]) for p in payments
    )

    # Aging buckets summary
    buckets: dict[str, int] = {}
    for p in payments:
        b = p["aging_bucket"]
        buckets[b] = buckets.get(b, 0) + p["amount_paise"]

    return {
        "overdue_count": len(payments),
        "total_overdue_paise": total_paise,
        "total_overdue_rupees": _paise_to_rupees(total_paise),
        "expected_recovery_paise": total_expected_recovery,
        "expected_recovery_rupees": _paise_to_rupees(total_expected_recovery),
        "payments": payments,
        "aging_buckets_paise": buckets,
        "data_as_of": datetime.now(UTC).isoformat(),
    }


def _recovery_probability(days_overdue: int, failed_count: int) -> float:
    """Heuristic recovery probability. Not an LLM opinion."""
    base = max(0.05, 0.85 - days_overdue * 0.008)
    penalty = min(0.3, failed_count * 0.08)
    return round(max(0.05, base - penalty), 3)


def _aging_bucket(days: int) -> str:
    if days <= 30:
        return "0-30 days"
    elif days <= 60:
        return "31-60 days"
    elif days <= 90:
        return "61-90 days"
    else:
        return "90+ days"


# ── Revenue variability (for financial readiness) ─────────────────────────────

async def get_revenue_variability(
    db: AsyncSession,
    merchant_id: str,
    months: int = 6,
) -> dict[str, Any]:
    """Compute coefficient of variation of monthly revenue."""
    from src.models.transaction import Transaction

    now = datetime.now(UTC)
    start = now - timedelta(days=months * 30)

    stmt = select(Transaction).where(
        and_(
            Transaction.merchant_id == merchant_id,
            Transaction.transaction_date >= start,
            Transaction.payment_status == "success",
        )
    )
    result = await db.execute(stmt)
    txns = result.scalars().all()

    if len(txns) < 10:
        return _unavailable("Insufficient data for variability calculation (< 10 transactions)")

    df = pd.DataFrame([{
        "month": t.transaction_date.strftime("%Y-%m"),
        "amount_paise": t.amount_paise,
    } for t in txns])

    monthly = df.groupby("month")["amount_paise"].sum()
    if len(monthly) < 2:
        return _unavailable("Need at least 2 months of data for variability")

    mean_rev = float(monthly.mean())
    std_rev = float(monthly.std())
    cv = std_rev / mean_rev if mean_rev > 0 else None

    return {
        "months_analyzed": len(monthly),
        "mean_monthly_revenue_paise": int(mean_rev),
        "std_monthly_revenue_paise": int(std_rev),
        "coefficient_of_variation": round(cv, 3) if cv else None,
        "stability": "stable" if cv and cv < 0.2 else "moderate" if cv and cv < 0.35 else "variable",
        "monthly_breakdown": monthly.to_dict(),
        "data_as_of": datetime.now(UTC).isoformat(),
    }


# ── Retention / repeat purchase rate ─────────────────────────────────────────

async def get_retention_metrics(
    db: AsyncSession,
    merchant_id: str,
    days: int = 30,
) -> dict[str, Any]:
    """Repeat purchase rate and new vs returning customer split."""
    from src.models.transaction import Transaction

    now = datetime.now(UTC)
    window_start = now - timedelta(days=days)

    stmt = select(Transaction).where(
        and_(
            Transaction.merchant_id == merchant_id,
            Transaction.transaction_date >= window_start,
            Transaction.payment_status == "success",
        )
    )
    result = await db.execute(stmt)
    txns = result.scalars().all()

    if not txns:
        return _unavailable("No successful transactions in window")
    df = pd.DataFrame([{"customer_id": t.customer_id} for t in txns])
    customer_counts = df["customer_id"].value_counts()
    repeat = int((customer_counts > 1).sum())
    total_unique = int(customer_counts.shape[0])
    repeat_rate = round(repeat / total_unique * 100, 1) if total_unique > 0 else 0

    return {
        "period_days": days,
        "unique_customers": total_unique,
        "repeat_customers": repeat,
        "repeat_purchase_rate": repeat_rate,
        "data_as_of": datetime.now(UTC).isoformat(),
    }
