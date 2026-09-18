# GrowthPilot AI — Build Status

*Last updated: Phase 4 complete (Foundations → Deployment)*

---

## ✅ Implemented & Tested

### Backend
- SQLite database with all 24 SQLAlchemy models
- Alembic migration environment
- Auth: Argon2 password hashing, JWT httpOnly cookies, RBAC
- Analytics engine: revenue, GMV, AOV, growth %, payment success rate
- Revenue change attribution (volume / AOV / customer mix / payment failure)
- Inactive customers using own-cadence definition (not fixed 30d)
- Inventory risks (days_until_stockout, restock qty formula shown)
- Overdue payments with aging buckets and recovery probability
- RFM segmentation (quintile-based, deterministic rules)
- Churn model (logistic regression, time-based split, no leakage)
- Sales forecasting (seasonal naive + Holt-Winters, rolling backtest)
- Opportunity engine: CUSTOMER_WINBACK, INVENTORY_RISK, PAYMENT_RECOVERY, REVENUE_DECLINE
- Explainability payloads (WHAT/WHY/EVIDENCE/IMPACT/CONFIDENCE/IF-APPROVE/RISKS)
- Policy Engine (L0–L4, kill switch, contact caps, quiet hours, reminder cooldown)
- Action state machine (all 11 states, illegal transitions raise errors)
- Idempotency key deduplication
- Simulated action executor (all labeled simulated=true)
- Independent verifier (re-reads DB, not executor return value)
- Hash-chained audit log with verify endpoint
- FastAPI routers: auth, dashboard, opportunities, actions, audit, assistant, missions
- Deterministic seed generator (SEED=42, same data every run)
- Scenario manifest with 7 planted scenarios

### Frontend
- Next.js 15 App Router with TypeScript
- Persistent SandboxBanner on every page
- Login page (pre-filled demo credentials)
- Dashboard: KPIs, revenue trend, opportunities, actions, inventory alerts
- Growth Opportunities page with explainability cards
- AI Command Center (mission creation + live step timeline)
- Action Center: list, detail, approve/reject with checklist
- Audit Log: timeline with hash chain verification indicator
- AI Assistant: intent detection + numeric grounding
- Inventory Intelligence: stock levels, demand, restock recommendations
- Collections Recovery: aging buckets, recovery probability
- Customers: inactive customer list with own-cadence data
- Analytics: revenue, attribution decomposition, retention metrics
- Financial Readiness: labeled "Demo eligibility — not a credit decision"
- Settings: autonomy dial, kill switch, quiet hours, reset demo
- Mobile bottom navigation (5 key routes)
- Dark/light mode (next-themes)

---

## 🔶 Mocked / Simulated

- **All external actions** — SMS, WhatsApp, payment links, restock orders, loan applications
  → `MockPaytmAdapter` in sandbox mode; labeled `simulated: true` everywhere
- **LLM explanations** — `MockLLM` template-based by default; real providers via env var
- **Payment links** — `sandbox.growthpilot.local/pay/...` format
- **Campaign sends** — logged to DB, labeled "Simulated send"
- **Financial Readiness** — "Demo eligibility" label; no real lenders
- **ML models trained on synthetic data** — metrics reported but not validated on real data

---

## ❌ Not Implemented

- Playwright E2E tests
- Real Paytm sandbox adapter (P2 — waiting for credentials)
- Voice input / Hindi/Hinglish STT (P2)
- Proof of Impact UI (control group measurement view) — backend logic present
- Multi-merchant switching UI (P2)
- Real UPI/soundbox integration (P2)
- Celery/Redis task queue (P2)
- Advanced bandit optimization (P2)
- Full ML integration tests with golden dataset

---

## Reliability Scorecard

| Check | Status |
|---|---|
| `/health` returns OK | ✅ |
| Sandbox badge visible | ✅ |
| Numbers from analytics engine | ✅ |
| Policy engine enforces L4 block | ✅ |
| Hash chain verifies | ✅ |
| Idempotency deduplication | ✅ |
| Simulated actions labeled | ✅ |
| Financial Readiness labeled | ✅ |
| Kill switch blocks actions | ✅ |
| LLM_PROVIDER=none works | ✅ |
