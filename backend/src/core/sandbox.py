"""
GrowthPilot Backend — Sandbox Mode Utilities
Helpers to mark simulated actions and enforce sandbox indicators.
"""
from src.core.config import settings


def is_sandbox() -> bool:
    """Returns True if running in sandbox/demo mode."""
    return settings.sandbox_mode


def sandbox_label() -> str:
    """Human-readable sandbox label for UI display."""
    return "Sandbox \u00b7 Synthetic Demo Data"


def mark_simulated(data: dict) -> dict:
    """
    Inject `simulated: true` and sandbox metadata into any API response dict.
    Called on all adapter responses that simulate external side-effects.
    """
    data["simulated"] = True
    data["sandbox_label"] = sandbox_label()
    return data


def fake_payment_link(payment_id: str) -> str:
    """Generate a clearly fake payment link URL for sandbox mode."""
    return f"https://sandbox.growthpilot.local/pay/{payment_id}"


def fake_sms_status(recipient_phone: str) -> dict:
    """Simulate an SMS send response."""
    return mark_simulated({
        "status": "sent",
        "recipient": f"***{recipient_phone[-4:]}",  # Mask PII
        "channel": "sms",
        "message_id": f"sim_sms_{recipient_phone[-4:]}",
    })


def fake_whatsapp_status(recipient_phone: str) -> dict:
    """Simulate a WhatsApp send response."""
    return mark_simulated({
        "status": "sent",
        "recipient": f"***{recipient_phone[-4:]}",
        "channel": "whatsapp",
        "message_id": f"sim_wa_{recipient_phone[-4:]}",
    })
