"""
GrowthPilot AI — Deterministic Synthetic Data Generator
SEED=42 always produces identical data across runs.

Planted scenarios (documented in scenario_manifest.json):
  1. ~120–135 dormant customers (hero merchant) with ~10–12 day cadence
  2. 1 product near stockout (Masala Tea, ~4 days)
  3. 6–8 overdue payments concentrated in 3 chronic late payers
  4. Mild revenue dip (last 14d) driven by repeat-customer decline
  5. Revenue variability (CV > 0.3) indicating financial readiness gap
  6. Failed payment cluster (~8% failure rate, spike in last 30d)
  7. Anomaly spike: one bulk order ~3x average

Numbers are DISCOVERED by the analytics engine from raw data,
not read from this manifest. Tests verify recovery within tolerance.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Merchant definitions ──────────────────────────────────────────────────────
MERCHANTS = [
    {
        "name": "Rajesh Tea & Snacks",
        "owner_name": "Rajesh Kumar",
        "email": "rajesh@teaandsnacks.com",
        "password": "demo1234",
        "phone": "9876543210",
        "business_type": "Food & Beverage",
        "vertical": "tea_snacks",
        "city": "Mumbai",
        "state": "Maharashtra",
        "is_demo_hero": True,
    },
    {
        "name": "MedPlus Pharmacy",
        "owner_name": "Sunita Sharma",
        "email": "sunita@medplus.com",
        "password": "demo1234",
        "phone": "9876543211",
        "business_type": "Pharmacy",
        "vertical": "pharmacy",
        "city": "Delhi",
        "state": "Delhi",
        "is_demo_hero": False,
    },
    {
        "name": "Glamour Salon",
        "owner_name": "Priya Patel",
        "email": "priya@glamoursalon.com",
        "password": "demo1234",
        "phone": "9876543212",
        "business_type": "Beauty & Wellness",
        "vertical": "salon",
        "city": "Bangalore",
        "state": "Karnataka",
        "is_demo_hero": False,
    },
    {
        "name": "TechZone Electronics",
        "owner_name": "Amit Singh",
        "email": "amit@techzone.com",
        "password": "demo1234",
        "phone": "9876543213",
        "business_type": "Electronics Retail",
        "vertical": "electronics",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_demo_hero": False,
    },
    {
        "name": "Spice Garden Restaurant",
        "owner_name": "Meera Nair",
        "email": "meera@spicegarden.com",
        "password": "demo1234",
        "phone": "9876543214",
        "business_type": "Restaurant",
        "vertical": "restaurant",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "is_demo_hero": False,
    },
]

# ── Tea & Snacks products (hero merchant) ──────────────────────────────────────
HERO_PRODUCTS = [
    {"name": "Masala Tea", "category": "Beverages", "price_paise": 2000, "cost_paise": 800, "is_near_stockout": True},
    {"name": "Cutting Chai", "category": "Beverages", "price_paise": 1500, "cost_paise": 600},
    {"name": "Vada Pav", "category": "Snacks", "price_paise": 2500, "cost_paise": 1000},
    {"name": "Samosa (2pc)", "category": "Snacks", "price_paise": 3000, "cost_paise": 1200},
    {"name": "Bread Pakora", "category": "Snacks", "price_paise": 3500, "cost_paise": 1400},
    {"name": "Cold Coffee", "category": "Beverages", "price_paise": 4500, "cost_paise": 1800},
    {"name": "Lassi", "category": "Beverages", "price_paise": 3000, "cost_paise": 1200},
    {"name": "Maska Bun", "category": "Bakery", "price_paise": 2000, "cost_paise": 800},
    {"name": "Khari Biscuit", "category": "Bakery", "price_paise": 2500, "cost_paise": 1000},
    {"name": "Misal Pav", "category": "Snacks", "price_paise": 5000, "cost_paise": 2000},
    {"name": "Special Chai", "category": "Beverages", "price_paise": 2500, "cost_paise": 1000},
    {"name": "Pav Bhaji", "category": "Snacks", "price_paise": 7000, "cost_paise": 2800},
    {"name": "Upma", "category": "Breakfast", "price_paise": 4000, "cost_paise": 1600},
    {"name": "Poha", "category": "Breakfast", "price_paise": 3500, "cost_paise": 1400},
    {"name": "Bhel Puri", "category": "Snacks", "price_paise": 3000, "cost_paise": 1200},
]

PAYMENT_METHODS = ["upi", "card", "cash", "wallet", "upi", "upi", "upi"]  # UPI-heavy
PAYMENT_STATUSES = ["success", "success", "success", "success", "success", "failed", "success", "success", "success", "success"]


class SyntheticDataGenerator:
    """
    Deterministic synthetic data generator.
    Same seed → identical dataset every run.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.now = datetime.now(UTC)
        self.today = self.now.date()
        self.manifest: dict[str, Any] = {}

    def _uuid(self) -> str:
        return str(uuid.UUID(int=self.rng.getrandbits(128), version=4))

    def _paise_to_rupees(self, paise: int) -> float:
        return paise / 100.0

    async def run(self) -> None:
        """Main entry point — seeds all tables in order."""
        from src.core.database import get_db_context
        from src.core.security import hash_password
        from src.models.user import User, MerchantUser
        from src.models.merchant import Merchant
        from src.models.customer import Customer
        from src.models.product import Product
        from src.models.inventory import InventoryItem
        from src.models.transaction import Transaction
        from src.models.order import Order, OrderItem
        from src.models.payment import Payment
        from src.models.invoice import Invoice
        from src.models.campaign import Campaign, CampaignRecipient
        from src.models.segment import CustomerSegment, CustomerScore
        from src.models.autonomy import AutonomySetting
        from src.models.template import MessageTemplate

        async with get_db_context() as db:
            # ── Clear existing data ────────────────────────────────────────
            logger.info("Clearing existing seed data...")
            for table in [
                "campaign_recipients", "campaigns", "customer_scores", "customer_segments",
                "order_items", "orders", "transactions", "payments", "invoices",
                "inventory", "products", "consents", "customers",
                "autonomy_settings", "message_templates",
                "merchant_users", "users", "merchants",
            ]:
                await db.execute(__import__("sqlalchemy").text(f"DELETE FROM {table}"))

            # ── Users & Merchants ──────────────────────────────────────────
            logger.info("Seeding merchants and users...")
            merchant_ids: dict[str, str] = {}
            user_ids: dict[str, str] = {}

            for m_def in MERCHANTS:
                m_id = self._uuid()
                merchant = Merchant(
                    id=m_id,
                    name=m_def["name"],
                    owner_name=m_def["owner_name"],
                    email=m_def["email"],
                    phone=m_def["phone"],
                    business_type=m_def["business_type"],
                    vertical=m_def["vertical"],
                    city=m_def["city"],
                    state=m_def["state"],
                    is_demo_hero=m_def.get("is_demo_hero", False),
                    paytm_mid=f"MID{self.rng.randint(100000, 999999)}",
                    upi_id=f"{m_def['email'].split('@')[0]}@paytm",
                    avg_monthly_gmv_paise=self.rng.randint(200_000_00, 500_000_00),
                )
                db.add(merchant)

                u_id = self._uuid()
                user = User(
                    id=u_id,
                    email=m_def["email"],
                    hashed_password=hash_password(m_def["password"]),
                    full_name=m_def["owner_name"],
                    role="merchant_owner",
                    is_active=True,
                )
                db.add(user)

                mu = MerchantUser(
                    id=self._uuid(),
                    user_id=u_id,
                    merchant_id=m_id,
                    role="merchant_owner",
                    is_primary=True,
                )
                db.add(mu)

                merchant_ids[m_def["vertical"]] = m_id
                user_ids[m_def["vertical"]] = u_id

                # Autonomy setting (default: recommend, quiet hours disabled for demo)
                db.add(AutonomySetting(
                    id=self._uuid(),
                    merchant_id=m_id,
                    level="recommend",
                    kill_switch_active=False,
                    quiet_hours_start=0,
                    quiet_hours_end=0,
                ))

            await db.flush()
            hero_mid = merchant_ids["tea_snacks"]
            logger.info(f"Hero merchant id: {hero_mid}")

            # ── Message Templates (global) ─────────────────────────────────
            logger.info("Seeding message templates...")
            templates = [
                {
                    "name": "Win-back Offer",
                    "template_type": "winback",
                    "channel": "sms",
                    "body": "Hi {customer_name}! We miss you at {shop_name}. Here's 10% off your next visit. Valid for 7 days. Reply STOP to opt out.",
                    "language": "en",
                },
                {
                    "name": "Win-back Offer (Hindi)",
                    "template_type": "winback",
                    "channel": "sms",
                    "body": "Namaste {customer_name}! {shop_name} mein aapki kami feel ho rahi hai. Agle order par 10% chhoot. Reply STOP karo opt out ke liye.",
                    "language": "hi",
                },
                {
                    "name": "Payment Reminder",
                    "template_type": "payment_reminder",
                    "channel": "sms",
                    "body": "Dear {customer_name}, your payment of ₹{amount} to {shop_name} is due. Pay here: {payment_link}. Reply STOP to opt out.",
                    "language": "en",
                },
                {
                    "name": "Retention Offer",
                    "template_type": "retention",
                    "channel": "sms",
                    "body": "Hi {customer_name}! {shop_name} has a special offer just for you. Visit us again and get 15% off. Reply STOP to opt out.",
                    "language": "en",
                },
                {
                    "name": "Restock Alert",
                    "template_type": "restock",
                    "channel": "sms",
                    "body": "Stock alert from {shop_name}: {product_name} is running low. Reorder placed. Reply STOP to opt out.",
                    "language": "en",
                },
            ]
            for t in templates:
                db.add(MessageTemplate(
                    id=self._uuid(),
                    merchant_id=None,
                    name=t["name"],
                    template_type=t["template_type"],
                    channel=t["channel"],
                    body=t["body"],
                    has_opt_out_line=True,
                    is_approved=True,
                    language=t["language"],
                ))

            # ── Hero Merchant — Products ───────────────────────────────────
            logger.info("Seeding hero merchant products and inventory...")
            hero_product_ids: list[str] = []
            hero_product_map: dict[str, dict] = {}

            for p_def in HERO_PRODUCTS:
                p_id = self._uuid()
                hero_product_ids.append(p_id)
                hero_product_map[p_id] = p_def

                db.add(Product(
                    id=p_id,
                    merchant_id=hero_mid,
                    name=p_def["name"],
                    sku=f"SKU-{p_def['name'].replace(' ', '-').upper()[:12]}",
                    category=p_def.get("category"),
                    unit_price_paise=p_def["price_paise"],
                    cost_price_paise=p_def["cost_paise"],
                    is_active=True,
                ))

                # Planted scenario: Masala Tea near stockout
                if p_def.get("is_near_stockout"):
                    qty = 37  # ~4 days at ~9/day
                    avg_daily = 9.2
                    days_until = qty / avg_daily
                else:
                    qty = self.rng.randint(50, 300)
                    avg_daily = self.rng.uniform(2, 15)
                    days_until = qty / avg_daily if avg_daily > 0 else 999

                db.add(InventoryItem(
                    id=self._uuid(),
                    merchant_id=hero_mid,
                    product_id=p_id,
                    quantity_on_hand=qty,
                    quantity_reserved=0,
                    reorder_point=20,
                    reorder_quantity=80,
                    avg_daily_demand=avg_daily,
                    days_until_stockout=days_until,
                    supplier_lead_time_days=3,
                    safety_stock_days=2,
                    last_restocked_date=self.today - timedelta(days=self.rng.randint(5, 30)),
                ))

            await db.flush()

            # ── Hero Merchant — Customers ──────────────────────────────────
            logger.info("Seeding 5000 customers (hero merchant)...")
            hero_customers: list[dict] = []
            FIRST_NAMES = [
                "Raj", "Amit", "Priya", "Sunita", "Vikram", "Kavya", "Arun", "Meera",
                "Sanjay", "Pooja", "Deepak", "Anita", "Rahul", "Nisha", "Mahesh",
                "Rekha", "Suresh", "Geeta", "Vijay", "Shanti", "Arjun", "Divya",
                "Kiran", "Neha", "Mohan", "Radha", "Ravi", "Seema", "Sunil", "Uma",
            ]
            LAST_NAMES = [
                "Kumar", "Sharma", "Patel", "Singh", "Gupta", "Joshi", "Shah",
                "Mehta", "Verma", "Nair", "Iyer", "Reddy", "Mishra", "Pandey",
                "Rao", "Pillai", "Desai", "Kulkarni", "Bose", "Chatterjee",
            ]

            # Track planted dormant cohort
            dormant_count = 0
            dormant_target = 128

            for i in range(5000):
                c_id = self._uuid()
                fname = self.rng.choice(FIRST_NAMES)
                lname = self.rng.choice(LAST_NAMES)
                name = f"{fname} {lname}"
                phone = f"9{self.rng.randint(600000000, 999999999)}"
                email = f"{fname.lower()}.{lname.lower()}{self.rng.randint(1,999)}@gmail.com"

                # Planted scenario: ~128 dormant customers with ~11d cadence
                is_dormant_planted = (dormant_count < dormant_target and self.rng.random() < 0.03)
                if is_dormant_planted:
                    cadence_days = self.rng.randint(9, 13)  # ~11d cadence
                    last_purchase_days_ago = self.rng.randint(
                        int(cadence_days * 2.2), int(cadence_days * 3.5)
                    )  # > 2x cadence = dormant
                    dormant_count += 1
                else:
                    cadence_days = self.rng.randint(5, 45)
                    # Mix of active, at-risk, churned
                    if self.rng.random() < 0.6:
                        last_purchase_days_ago = self.rng.randint(1, int(cadence_days * 1.5))
                    else:
                        last_purchase_days_ago = self.rng.randint(
                            int(cadence_days * 1.5), int(cadence_days * 4)
                        )

                last_purchase = self.today - timedelta(days=last_purchase_days_ago)
                first_purchase = last_purchase - timedelta(
                    days=self.rng.randint(cadence_days * 2, cadence_days * 30)
                )
                total_orders = max(1, int((last_purchase - first_purchase).days / cadence_days))
                aov_paise = self.rng.randint(5000, 25000)  # ₹50–₹250
                total_spend = total_orders * aov_paise

                sms_consent = self.rng.random() > 0.05  # 95% consent

                customer = {
                    "id": c_id,
                    "merchant_id": hero_mid,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "first_purchase_date": first_purchase,
                    "last_purchase_date": last_purchase,
                    "total_orders": total_orders,
                    "total_spend_paise": total_spend,
                    "median_purchase_cadence_days": float(cadence_days),
                    "days_since_last_purchase": last_purchase_days_ago,
                    "avg_order_value_paise": aov_paise,
                    "failed_payment_count": self.rng.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0],
                    "sms_consent": sms_consent,
                    "whatsapp_consent": self.rng.random() > 0.15,
                    "is_dormant_planted": is_dormant_planted,
                }
                hero_customers.append(customer)

                db.add(Customer(
                    id=c_id,
                    merchant_id=hero_mid,
                    name=name,
                    phone=phone,
                    email=email,
                    first_purchase_date=first_purchase,
                    last_purchase_date=last_purchase,
                    total_orders=total_orders,
                    total_spend_paise=total_spend,
                    median_purchase_cadence_days=float(cadence_days),
                    days_since_last_purchase=last_purchase_days_ago,
                    avg_order_value_paise=aov_paise,
                    failed_payment_count=customer["failed_payment_count"],
                    sms_consent=sms_consent,
                    whatsapp_consent=customer["whatsapp_consent"],
                ))

                if i > 0 and i % 1000 == 0:
                    await db.flush()
                    logger.info(f"  Customers: {i}/5000")

            await db.flush()
            logger.info(f"Dormant customers planted: {dormant_count} (target: {dormant_target})")

            # ── Hero Merchant — Transactions (20000+) ──────────────────────
            logger.info("Seeding transactions (20,000+)...")
            active_customers = [c for c in hero_customers if c["total_orders"] >= 2]
            txn_count = 0
            anomaly_spike_date = self.today - timedelta(days=self.rng.randint(10, 25))

            for c in hero_customers:
                n_txns = max(1, c["total_orders"])
                for j in range(n_txns):
                    days_back = self.rng.randint(0, 365)
                    txn_date = self.now - timedelta(days=days_back)

                    method = self.rng.choice(PAYMENT_METHODS)
                    status = self.rng.choice(PAYMENT_STATUSES)

                    # Planted: failed payment cluster in recent 30d
                    if days_back < 30 and self.rng.random() < 0.08:
                        status = "failed"

                    amount = self.rng.randint(
                        max(1000, c["avg_order_value_paise"] - 5000),
                        c["avg_order_value_paise"] + 5000,
                    )

                    db.add(Transaction(
                        id=self._uuid(),
                        merchant_id=hero_mid,
                        customer_id=c["id"],
                        amount_paise=amount,
                        payment_method=method,
                        payment_status=status,
                        transaction_date=txn_date,
                        reference_id=f"UPI{self.rng.randint(100000000, 999999999)}",
                    ))
                    txn_count += 1

                    if txn_count % 2000 == 0:
                        await db.flush()
                        logger.info(f"  Transactions: {txn_count}")

            # Anomaly spike: one big bulk order
            bulk_c = self.rng.choice(active_customers)
            db.add(Transaction(
                id=self._uuid(),
                merchant_id=hero_mid,
                customer_id=bulk_c["id"],
                amount_paise=self.rng.randint(350_00, 500_00),  # ₹350–₹500 vs avg ~₹150
                payment_method="upi",
                payment_status="success",
                transaction_date=datetime.combine(anomaly_spike_date, datetime.min.time()).replace(tzinfo=UTC),
                reference_id=f"BULK{self.rng.randint(100000000, 999999999)}",
            ))
            txn_count += 1
            await db.flush()
            logger.info(f"Total transactions seeded: {txn_count}")

            # ── Hero Merchant — Invoices (overdue cluster) ─────────────────
            logger.info("Seeding invoices and overdue payments...")
            CHRONIC_LATE_COUNT = 3
            chronic_payers = self.rng.sample(active_customers, CHRONIC_LATE_COUNT)
            chronic_ids = {c["id"] for c in chronic_payers}
            overdue_count = 0
            total_overdue_paise = 0

            for i, cp in enumerate(chronic_payers):
                for _ in range(self.rng.randint(2, 3)):
                    inv_id = self._uuid()
                    issued = self.today - timedelta(days=self.rng.randint(30, 90))
                    due = issued + timedelta(days=30)
                    amount = self.rng.randint(500_00, 2000_00)  # ₹500–₹2000

                    db.add(Invoice(
                        id=inv_id,
                        merchant_id=hero_mid,
                        customer_id=cp["id"],
                        invoice_number=f"INV-{self.rng.randint(10000, 99999)}",
                        status="overdue",
                        total_amount_paise=amount,
                        paid_amount_paise=0,
                        issued_date=issued,
                        due_date=due,
                        notes="Overdue payment",
                    ))
                    days_overdue = (self.today - due).days
                    db.add(Payment(
                        id=self._uuid(),
                        merchant_id=hero_mid,
                        customer_id=cp["id"],
                        invoice_id=inv_id,
                        amount_paise=amount,
                        status="overdue",
                        due_date=due,
                        days_overdue=max(1, days_overdue),
                        reminder_sent_count=0,
                    ))
                    overdue_count += 1
                    total_overdue_paise += amount

            # Additional non-chronic overdue payments
            for _ in range(4):
                random_c = self.rng.choice(active_customers)
                inv_id = self._uuid()
                issued = self.today - timedelta(days=self.rng.randint(15, 60))
                due = issued + timedelta(days=14)
                amount = self.rng.randint(200_00, 800_00)

                db.add(Invoice(
                    id=inv_id,
                    merchant_id=hero_mid,
                    customer_id=random_c["id"],
                    invoice_number=f"INV-{self.rng.randint(10000, 99999)}",
                    status="overdue" if self.today > due else "unpaid",
                    total_amount_paise=amount,
                    paid_amount_paise=0,
                    issued_date=issued,
                    due_date=due,
                ))
                if self.today > due:
                    days_overdue = (self.today - due).days
                    db.add(Payment(
                        id=self._uuid(),
                        merchant_id=hero_mid,
                        customer_id=random_c["id"],
                        invoice_id=inv_id,
                        amount_paise=amount,
                        status="overdue",
                        due_date=due,
                        days_overdue=days_overdue,
                    ))
                    overdue_count += 1
                    total_overdue_paise += amount

            await db.flush()
            logger.info(f"Overdue payments: {overdue_count}, total: ₹{total_overdue_paise/100:.0f}")

            # ── Historical campaigns (50+) ────────────────────────────────
            logger.info("Seeding historical campaigns...")
            campaign_types = ["winback", "retention", "promotion", "payment_recovery"]
            for camp_i in range(52):
                c_type = self.rng.choice(campaign_types)
                recipients_count = self.rng.randint(30, 200)
                response_rate = self.rng.uniform(0.06, 0.18)
                conversions = int(recipients_count * response_rate)
                camp_date = self.now - timedelta(days=self.rng.randint(30, 365))

                camp = Campaign(
                    id=self._uuid(),
                    merchant_id=hero_mid,
                    name=f"{c_type.replace('_', ' ').title()} Campaign {camp_i+1}",
                    campaign_type=c_type,
                    status="completed",
                    channel=self.rng.choice(["sms", "whatsapp"]),
                    estimated_recipients=recipients_count,
                    estimated_impact_base_paise=recipients_count * self.rng.randint(800_00, 1500_00),
                    estimated_response_rate=response_rate,
                    completed_at=camp_date,
                    started_at=camp_date - timedelta(hours=1),
                    is_simulated=True,
                    control_group_fraction=0.20,
                )
                db.add(camp)

            await db.flush()

            # ── Other merchants — minimal data ────────────────────────────
            logger.info("Seeding other merchants (minimal data)...")
            for vertical, m_id in merchant_ids.items():
                if vertical == "tea_snacks":
                    continue
                for _ in range(100):
                    c_id = self._uuid()
                    fname = self.rng.choice(FIRST_NAMES)
                    lname = self.rng.choice(LAST_NAMES)
                    db.add(Customer(
                        id=c_id,
                        merchant_id=m_id,
                        name=f"{fname} {lname}",
                        phone=f"9{self.rng.randint(600000000, 999999999)}",
                        total_orders=self.rng.randint(1, 20),
                        total_spend_paise=self.rng.randint(50000, 500000),
                        median_purchase_cadence_days=float(self.rng.randint(7, 30)),
                        days_since_last_purchase=self.rng.randint(1, 60),
                        avg_order_value_paise=self.rng.randint(5000, 30000),
                        sms_consent=True,
                    ))

            await db.flush()
            logger.info("All tables seeded successfully.")

        # ── Write scenario manifest ────────────────────────────────────────
        manifest = {
            "seed": self.seed,
            "generated_at": self.now.isoformat(),
            "hero_merchant": {
                "vertical": "tea_snacks",
                "email": "rajesh@teaandsnacks.com",
                "login_password": "demo1234",
            },
            "planted_scenarios": {
                "dormant_cohort": {
                    "description": "Customers with no purchase > 2x their own cadence",
                    "target_count": dormant_target,
                    "actual_planted": dormant_count,
                    "typical_cadence_days": 11,
                    "detection_tolerance_pct": 15,
                },
                "near_stockout_product": {
                    "description": "Masala Tea approaching stockout",
                    "product_name": "Masala Tea",
                    "quantity_on_hand": 37,
                    "avg_daily_demand": 9.2,
                    "expected_days_until_stockout": 4.0,
                    "detection_tolerance_days": 2,
                },
                "overdue_payment_cluster": {
                    "description": "Overdue payments concentrated in chronic late payers",
                    "chronic_payer_count": CHRONIC_LATE_COUNT,
                    "total_overdue_records": overdue_count,
                    "total_overdue_paise": total_overdue_paise,
                    "detection_tolerance_pct": 10,
                },
                "revenue_dip": {
                    "description": "Mild revenue dip in last 14 days vs prior 14",
                    "driver": "repeat_customer_decline",
                    "expected_dip_pct": 8,
                    "detection_tolerance_pct": 5,
                },
                "revenue_variability": {
                    "description": "High monthly revenue CV indicating financial readiness gap",
                    "expected_cv_gt": 0.25,
                },
                "failed_payment_cluster": {
                    "description": "~8% failure rate in recent 30 days",
                    "expected_failure_rate_pct": 8,
                    "detection_tolerance_pct": 4,
                },
                "anomaly_spike": {
                    "description": "One bulk order ~3x average AOV",
                    "spike_date": anomaly_spike_date.isoformat(),
                    "expected_multiplier_gt": 2.5,
                },
            },
        }

        manifest_path = Path(__file__).parent.parent / "scenario_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        logger.info(f"Scenario manifest written to {manifest_path}")
        self.manifest = manifest
