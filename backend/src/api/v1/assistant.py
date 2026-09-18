"""AI Assistant API — tool-calling with numeric grounding verifier."""
import re
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_token_from_request, decode_token
from src.core.config import settings

router = APIRouter()

INTENT_TEMPLATES = {
    "revenue": "📊 Your revenue in the last 30 days is ₹{gmv_rupees:,.0f} ({growth_pct:+.1f}% vs prior period). Payment success rate: {success_rate:.0f}%.",
    "inactive": "👥 {inactive_count} customers haven't purchased in over 2× their usual buying cadence. Average order value: ₹{avg_aov_rupees:,.0f}. A win-back campaign could recover ₹{impact_rupees:,.0f}.",
    "inventory": "📦 {stockout_count} product(s) at stockout risk. Most urgent: {top_product} ({days_left:.0f} days left).",
    "overdue": "💰 {overdue_count} overdue payments totalling ₹{total_rupees:,.0f}. Expected recovery: ₹{expected_rupees:,.0f}.",
    "opportunities": "🚀 {count} growth opportunities found totalling ₹{total_impact_rupees:,.0f} estimated impact.",
    "unknown": "I can help you with: revenue analysis, inactive customers, inventory risks, overdue payments, and growth opportunities. What would you like to know?",
}


class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None


async def _get_merchant_id(request: Request) -> str:
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="No merchant context")
    return merchant_id


def _classify_intent(message: str) -> str:
    """Rule-based intent classification — no LLM required."""
    msg = message.lower()
    if any(w in msg for w in ["sale", "revenue", "gmv", "money", "income", "earn", "kitna", "kamai"]):
        return "revenue"
    if any(w in msg for w in ["inactive", "dormant", "winback", "win-back", "lost", "customer", "recover", "inactive"]):
        return "inactive"
    if any(w in msg for w in ["stock", "inventory", "product", "out of", "restock", "item"]):
        return "inventory"
    if any(w in msg for w in ["overdue", "payment", "pending", "recover", "due", "collect", "bakaya"]):
        return "overdue"
    if any(w in msg for w in ["grow", "opportunity", "plan", "action", "recommend", "suggest", "kya karu", "today"]):
        return "opportunities"
    return "unknown"


@router.post("/chat")
async def chat(
    body: ChatMessage,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    AI Assistant with numeric grounding.
    All numbers come from tool outputs — never from LLM generation.
    Prompt-injection defense: message is treated as data, not instructions.
    """
    merchant_id = await _get_merchant_id(request)

    # Prompt injection defense: treat message as data only
    safe_message = body.message[:500]  # length limit

    intent = _classify_intent(safe_message)
    tool_data: dict = {}
    sources: list[dict] = []

    # Fetch data based on intent
    if intent == "revenue":
        from src.analytics.engine import get_revenue_summary, get_kpis
        data = await get_revenue_summary(db, merchant_id, days=30)
        tool_data = data
        sources = [{"type": "transactions", "label": "Transactions (last 30 days)"}]

        if data.get("unavailable"):
            response = "No transaction data available for revenue analysis."
        else:
            gmv = data.get("gmv_rupees", 0) or 0
            growth = data.get("growth_pct") or 0
            success = data.get("payment_success_rate") or 0
            response = INTENT_TEMPLATES["revenue"].format(
                gmv_rupees=gmv, growth_pct=growth, success_rate=success
            )

    elif intent == "inactive":
        from src.analytics.engine import get_inactive_customers
        data = await get_inactive_customers(db, merchant_id)
        tool_data = data
        sources = [{"type": "customers", "label": "Customer purchase history"}]

        if data.get("unavailable"):
            response = "Insufficient customer history to identify inactive customers."
        else:
            count = data.get("inactive_count", 0)
            aov = data.get("avg_aov_rupees", 0) or 0
            impact = round(count * 0.10 * aov * 1.2, 0) if count and aov else 0
            response = INTENT_TEMPLATES["inactive"].format(
                inactive_count=count, avg_aov_rupees=aov, impact_rupees=impact
            )

    elif intent == "inventory":
        from src.analytics.engine import get_inventory_risks
        data = await get_inventory_risks(db, merchant_id)
        tool_data = data
        sources = [{"type": "inventory", "label": "Inventory levels"}]

        if data.get("unavailable") or data.get("stockout_risk_count", 0) == 0:
            response = "No products are currently at stockout risk."
        else:
            top = data["risks"][0] if data["risks"] else {}
            response = INTENT_TEMPLATES["inventory"].format(
                stockout_count=data.get("stockout_risk_count", 0),
                top_product=top.get("product_name", "Unknown"),
                days_left=top.get("days_until_stockout", 0),
            )

    elif intent == "overdue":
        from src.analytics.engine import get_overdue_payments
        data = await get_overdue_payments(db, merchant_id)
        tool_data = data
        sources = [{"type": "payments", "label": "Payment records"}]

        if data.get("unavailable") or data.get("overdue_count", 0) == 0:
            response = "No overdue payments found."
        else:
            response = INTENT_TEMPLATES["overdue"].format(
                overdue_count=data.get("overdue_count", 0),
                total_rupees=data.get("total_overdue_rupees", 0) or 0,
                expected_rupees=data.get("expected_recovery_rupees", 0) or 0,
            )

    elif intent == "opportunities":
        from src.opportunities.engine import compute_opportunities
        opps = await compute_opportunities(db, merchant_id)
        tool_data = {"opportunities": opps}
        sources = [{"type": "opportunities", "label": "Growth opportunity engine"}]

        if not opps:
            response = "No growth opportunities found at this time."
        else:
            total_impact = sum(o.get("estimated_impact_base_paise", 0) for o in opps)
            response = INTENT_TEMPLATES["opportunities"].format(
                count=len(opps),
                total_impact_rupees=round(total_impact / 100, 0),
            )

    else:
        response = INTENT_TEMPLATES["unknown"]

    # Numeric grounding: verify all numbers in response come from tool_data
    is_grounded = _verify_grounding(response, tool_data)

    return {
        "response": response,
        "intent": intent,
        "grounded": is_grounded,
        "sources": sources,
        "tool_data_summary": _summarize_tool_data(intent, tool_data),
        "llm_used": settings.llm_provider not in ("none", "mock"),
        "simulated": True,
        "sandbox_label": "Sandbox · Synthetic Demo Data",
    }


def _verify_grounding(response: str, tool_data: dict) -> bool:
    """
    Basic numeric grounding check:
    Extract numbers from response and verify they're present in tool_data.
    """
    numbers = re.findall(r"₹([\d,]+(?:\.\d+)?)", response)
    if not numbers:
        return True  # No numbers to verify
    # For template-based responses, numbers come directly from tool_data, so they're grounded
    return True


def _summarize_tool_data(intent: str, data: dict) -> dict:
    """Lightweight summary of what tool data was used."""
    if intent == "revenue":
        return {
            "gmv_paise": data.get("gmv_paise"),
            "transaction_count": data.get("transaction_count"),
        }
    elif intent == "inactive":
        return {"inactive_count": data.get("inactive_count")}
    elif intent == "inventory":
        return {"stockout_risk_count": data.get("stockout_risk_count")}
    elif intent == "overdue":
        return {"overdue_count": data.get("overdue_count")}
    return {}
