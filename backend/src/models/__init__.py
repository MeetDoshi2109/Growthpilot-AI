"""
GrowthPilot Backend — All SQLAlchemy Models
Imports all models so Alembic and create_all_tables() can discover them.
"""
from src.core.database import Base  # noqa: F401 — Base must be imported first

from src.models.user import User, MerchantUser  # noqa: F401
from src.models.merchant import Merchant  # noqa: F401
from src.models.customer import Customer  # noqa: F401
from src.models.product import Product  # noqa: F401
from src.models.inventory import InventoryItem  # noqa: F401
from src.models.transaction import Transaction  # noqa: F401
from src.models.order import Order, OrderItem  # noqa: F401
from src.models.payment import Payment  # noqa: F401
from src.models.invoice import Invoice  # noqa: F401
from src.models.campaign import Campaign, CampaignRecipient  # noqa: F401
from src.models.segment import CustomerSegment, CustomerScore  # noqa: F401
from src.models.opportunity import GrowthOpportunity  # noqa: F401
from src.models.agent import AgentTask, AgentAction, ActionApproval  # noqa: F401
from src.models.audit import AuditLog  # noqa: F401
from src.models.financial import FinancialProfile  # noqa: F401
from src.models.notification import Notification  # noqa: F401
from src.models.consent import Consent  # noqa: F401
from src.models.impact import ImpactMeasurement  # noqa: F401
from src.models.model_run import ModelRun  # noqa: F401
from src.models.idempotency import IdempotencyKey  # noqa: F401
from src.models.mission import Mission, MissionStep  # noqa: F401
from src.models.autonomy import AutonomySetting  # noqa: F401
from src.models.template import MessageTemplate  # noqa: F401

__all__ = [
    "Base",
    "User", "MerchantUser",
    "Merchant",
    "Customer",
    "Product",
    "InventoryItem",
    "Transaction",
    "Order", "OrderItem",
    "Payment",
    "Invoice",
    "Campaign", "CampaignRecipient",
    "CustomerSegment", "CustomerScore",
    "GrowthOpportunity",
    "AgentTask", "AgentAction", "ActionApproval",
    "AuditLog",
    "FinancialProfile",
    "Notification",
    "Consent",
    "ImpactMeasurement",
    "ModelRun",
    "IdempotencyKey",
    "Mission", "MissionStep",
    "AutonomySetting",
    "MessageTemplate",
]
